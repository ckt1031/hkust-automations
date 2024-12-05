import sys
from datetime import datetime, timezone

from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

import lib.env as env
from discord.webhook import send_discord
from email_summarizer.email_extractor import EmailExtractor
from email_summarizer.email_record import prune_email_record
from lib.llm import llm_generate
from lib.onedrive_store import EMAIL_RECORD_PATH, get_store, save_store
from prompts.email_summarize import email_summary_prompt


def email_summarize():
    webhook_url = env.DISCORD_WEBHOOK_URL_EMAILS

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

    mail_records = get_store(EMAIL_RECORD_PATH)

    # Prune the email record to remove emails older than 7 days
    mail_records = prune_email_record(mail_records)

    # Check if some email is checked
    for email in emails:
        checked = email["id"] in mail_records

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

        mail_records[email["id"]] = current_time

    # Save the email record
    save_store(EMAIL_RECORD_PATH, mail_records)

    logger.success("All emails are checked")
