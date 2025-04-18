import textwrap
from datetime import datetime, timezone

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from lib.api.discord import send_discord_webhook
from lib.api.onedrive import get_store_with_datetime, save_store_with_datetime
from lib.api.openai import generate_schema
from lib.env import getenv
from lib.outlook.extractor import EmailExtractor
from lib.outlook.store import prune_email_store
from lib.prompts.email_summary import EmailSummarySchema, email_summary_prompt
from lib.utils import check_if_arg_exists


def wrap_all_markdown_link(text: str) -> str:
    """
    Wrap the text with markdown link format.

    Args:
        text (str): The text to wrap.

    Returns:
        str: The wrapped text.
    """
    import re

    return re.sub(
        r"(\[.*?\]\()(.*?)(\))",
        lambda m: f"{m.group(1)}<{m.group(2)}>{m.group(3)}",
        text,
    )


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

    # Is Debugging
    is_debug = check_if_arg_exists("--debug")

    # Check if some email is checked
    for email in emails:
        checked = email["id"] in store

        if checked and not is_debug:
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

            # Send the summary to Discord if not in debug mode
            if not is_debug:
                split_text_and_send_to_discord(summary.strip(), webhook_url)

                logger.success("Discord webhook sent successfully")

        # Save debug summaries to local txt files
        if is_debug:
            text = f"""
========== Info Summary Debugging ==========\n\n
{llm_response.info_summary.strip()}\n\n
========== Event Summary Debugging ==========\n\n
{llm_response.event_summary.strip()}\n\n
========== Opportunities Summary Debugging ==========\n\n
{llm_response.opportunities_summary.strip()}
            """
            with open("./debug/email_summary.txt", "w") as f:
                f.write(wrap_all_markdown_link(text.strip()))

            logger.success("Debug summaries saved to debug_email_summary.txt")

    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in checking_emails:
        store[email["id"]] = datetime.now(tz=timezone.utc)

    # Save the email store only if not in debug mode
    if not is_debug:
        save_store_with_datetime(store_path, store)

    logger.success(f"{len(checking_emails)} Outlook emails are checked")
