import textwrap
from datetime import datetime, timezone

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from lib.discord_webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from lib.outlook.extractor import EmailExtractor
from lib.outlook.store import prune_email_store
from lib.prompts.email_summarize import EmailSummarySchema, email_summary_prompt


def split_text_and_send_to_discord(text: str, webhook_url: str):
    headers_to_split_on = [
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        strip_headers=False,
        headers_to_split_on=headers_to_split_on,
    )
    result = markdown_splitter.split_text(text)

    chunk_size = 1900
    chunk_overlap = 100
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    result = text_splitter.split_documents(result)

    for split in result:
        send_discord_webhook(
            webhook_url, message=split.page_content, username="HKUST Email"
        )


def summarize_outlook():
    # Get the webhook URLs
    webhook_url_email = getenv("DISCORD_WEBHOOK_URL_EMAILS", required=True)
    webhook_url_events = getenv("DISCORD_WEBHOOK_URL_EMAILS_EVENTS", required=True)
    webhook_url_opportunities = getenv(
        "DISCORD_WEBHOOK_URL_EMAILS_OPPORTUNITIES", required=True
    )

    # Extract emails
    emails = EmailExtractor().extract_emails()

    # YYYY-MM-DD (Weekday)
    today_date = datetime.now().strftime("%Y-%m-%d (%A)")
    email_user_prompt = f"Current Date: {today_date}\n\n"

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
        summaries = [
            [llm_response.info_summary, webhook_url_email],
            [llm_response.event_summary, webhook_url_events],
            [llm_response.opportunities_summary, webhook_url_opportunities],
        ]

        for summary_data in summaries:
            if len(summary_data[0]) == 0:
                logger.info("No text to send to Discord")
                continue

            if summary_data[0].startswith("{"):
                raise ValueError("Response is not a valid string content")

            split_text_and_send_to_discord(summary_data[0].strip(), summary_data[1])

        logger.success("Email summary sent to Discord")

    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in checking_emails:
        store[email["id"]] = datetime.now(tz=timezone.utc)

    # Save the email store
    save_store_with_datetime(store_path, store)

    logger.success(f"{len(checking_emails)} Outlook emails are checked")
