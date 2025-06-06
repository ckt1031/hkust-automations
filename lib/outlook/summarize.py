import textwrap
from datetime import datetime, timezone

from loguru import logger

from lib.api.onedrive import get_store_with_datetime, save_store_with_datetime
from lib.api.openai import generate_schema
from lib.env import getenv
from lib.outlook.extractor import EmailExtractor
from lib.outlook.store import prune_email_store
from lib.prompts.email_summary import EmailSummarySchema, email_summary_prompt
from lib.utils import split_text_and_send_to_discord, wrap_all_markdown_link


def summarize_outlook():
    """
    Summarize Outlook emails and send the summary to Discord.

    Debug mode: All emails are passed to the LLM for summarization, saved to local txt files, but it will not send to Discord and save to the database.
    """
    # Get the webhook URLs
    webhook_url_info = getenv("DISCORD_WEBHOOK_EMAIL_INFO", required=True)
    webhook_url_events = getenv("DISCORD_WEBHOOK_EMAIL_EVENT", required=True)
    webhook_url_program = getenv("DISCORD_WEBHOOK_EMAIL_PROGRAM", required=True)

    # Extract emails
    emails = EmailExtractor().extract_emails()

    # YYYY-MM-DD HH:MM:SS (Day)
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")
    email_user_prompt = f"Current Datetime: {current_datetime}\n\n"

    store_path = "email_record.json"
    store = get_store_with_datetime(store_path)
    # Prune the email store to remove emails older than 7 days
    store = prune_email_store(store)

    checking_emails = []

    # Check if some email is checked
    for email in emails:
        checked = email["id"] in store

        if checked:
            logger.debug(
                f"Email {email['id']} ({email['subject']}) was checked, skipping"
            )
            continue

        # Basic information about the email
        prompt = (
            f"Subject: {email['subject']}\nFrom: {email['from']}\nDate: {email['date']}"
        )
        # Main body
        prompt += (
            f"\n\n--- Main Body START ---\n\n{email['body']}\n\n--- Main Body END ---"
        )

        if email["is_reply"] and len(email["replies_body"]) > 0:
            # Add the replies to the email
            for reply in email["replies_body"]:
                # Label the reply number for LLM to understand the context
                index = email["replies_body"].index(reply) + 1
                reply_content = f"Subject: {reply['subject']}\nFrom: {reply['from']}\nDate: {reply['date']}\n\n{reply['body']}"

                # Wrap it up
                reply_content = f"\n\n--- Reply {index} START ---\n\n{reply_content}\n\n--- Reply {index} END ---"

                # Indent the reply content
                prompt += textwrap.indent(reply_content, "    ")

        index = len(checking_emails) + 1
        email_user_prompt += f"==== Email {index} START ====\n\n{prompt}\n\n==== Email {index} END ====\n\n"

        checking_emails.append(email)

    # If there are no unchecked emails, exit the program
    if len(checking_emails) == 0:
        logger.success("No new emails to summarize")
        return

    # Call the LLM model to summarize the emails
    llm_response = generate_schema(
        system_message=email_summary_prompt,
        user_message=email_user_prompt,
        schema=EmailSummarySchema,
    )

    if llm_response.available:
        categorized_summaries_data = [
            [llm_response.info_summary, webhook_url_info],
            [llm_response.event_summary, webhook_url_events],
            [llm_response.opportunities_summary, webhook_url_program],
        ]

        for data in categorized_summaries_data:
            summary = data[0]
            webhook_url = data[1]

            # Skip if the summary is empty
            if summary is None or len(summary) == 0:
                logger.warning("Summary is empty, skipping")
                continue

            # Process the summary text
            summary = wrap_all_markdown_link(summary)

            # Send the summary to Discord
            split_text_and_send_to_discord(summary.strip(), webhook_url)

            logger.success("Discord webhook sent successfully")

    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in checking_emails:
        store[email["id"]] = datetime.now(tz=timezone.utc)

    # Save the email store
    save_store_with_datetime(store_path, store)

    logger.success(f"{len(checking_emails)} Outlook emails are checked")
