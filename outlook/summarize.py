import sys
from datetime import datetime, timezone

from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

import lib.env as env
from discord.webhook import send_discord
from lib.llm import llm_generate
from lib.onedrive_store import get_store, save_store
from outlook.extractor import EmailExtractor
from outlook.store import prune_email_store
from prompts.email_summarize import email_summary_prompt


def email_summarize():
    webhook_url = env.DISCORD_WEBHOOK_URL_EMAILS
    store_path = f"{env.ONEDRIVE_STORE_FOLDER}/email_record.json"

    if webhook_url is None:
        logger.error(
            "Discord webhook URL is not provided in the environment variables (DISCORD_WEBHOOK_URL_EMAILS)"
        )
        sys.exit(1)

    # Initialize the email client
    extractor = EmailExtractor()
    emails = extractor.extract_emails()

    # YYYY-MM-DD
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_day = datetime.now().strftime("%A")  # Monday, Tuesday, etc.

    email_user_prompt = f"""
    Date: {today_date}
    Day: {today_day}

    Emails:
    """

    unchecked_email_amount = 0

    store = get_store(store_path)

    # Prune the email store to remove emails older than 7 days
    store = prune_email_store(store)

    # Check if some email is checked
    for email in emails:
        checked = email["id"] in store

        if checked:
            logger.info(f"Email {email['id']} was checked, skipping")

            # Remove the email from the list
            emails.remove(email)
            continue

        email_user_prompt += f"\n\n\nSubject: {email['subject']}\nFrom: {email['from']}\nBody: {email['body']}"
        unchecked_email_amount += 1

    # If there are no unchecked emails, exit the program
    if unchecked_email_amount == 0:
        logger.success("No unchecked emails found")
        return

    # Call the LLM model to summarize the emails
    llm_response = llm_generate(email_summary_prompt, email_user_prompt)

    if llm_response.strip().lower() != "no":
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=False
        )
        result = markdown_splitter.split_text(llm_response)

        for split in result:
            send_discord(webhook_url, split.page_content, None, "HKUST Email")

        logger.success("Email summary sent to Discord")

    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in emails:
        current_time = datetime.now(tz=timezone.utc)

        store[email["id"]] = current_time

    # Save the email store
    save_store(store_path, store)

    logger.success("All emails are checked")
