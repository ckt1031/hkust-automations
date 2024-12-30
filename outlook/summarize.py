from datetime import datetime, timezone

from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from outlook.extractor import EmailExtractor
from outlook.store import prune_email_store
from prompts.email_summarize import EmailSummarySchema, email_summary_prompt


def email_summarize():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_EMAILS")

    if webhook_url is None:
        raise ValueError(
            "DISCORD_WEBHOOK_URL_EMAILS is not provided in the environment variables"
        )

    # Initialize the email client
    extractor = EmailExtractor()
    emails = extractor.extract_emails()

    # YYYY-MM-DD
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_day = datetime.now().strftime("%A")  # Monday, Tuesday, etc.

    email_user_prompt = f"Date: {today_date}\nWeekday: {today_day}\n\n---\n\n"

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

        email_user_prompt += f"Subject: {email['subject']}\nFrom: {email['from']}\nBody:\n\n{email['body']}\n\n---\n\n"
        checking_emails.append(email)

    # If there are no unchecked emails, exit the program
    if len(checking_emails) == 0:
        logger.success("No unchecked emails found")
        return

    # Call the LLM model to summarize the emails
    llm_response = generate_schema(
        email_summary_prompt, email_user_prompt, EmailSummarySchema
    )

    if llm_response.available:
        headers_to_split_on = [
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            strip_headers=False,
            headers_to_split_on=headers_to_split_on,
        )
        result = markdown_splitter.split_text(llm_response.summary)

        for split in result:
            send_discord_webhook(
                webhook_url, message=split.page_content, username="HKUST Email"
            )

        logger.success("Email summary sent to Discord")

    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in checking_emails:
        current_time = datetime.now(tz=timezone.utc)
        store[email["id"]] = current_time

    # Save the email store
    save_store_with_datetime(store_path, store)

    logger.success(f"{len(checking_emails)} Outlook emails are checked")
