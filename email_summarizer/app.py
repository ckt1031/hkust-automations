import sys
from datetime import datetime

from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

import lib.env as env
from email_summarizer.email_extractor import EmailExtractor
from email_summarizer.email_record import mark_email_as_checked, prune_email_record
from lib.llm import LLM
from lib.notification import send_discord
from lib.onedrive_store import (
    EMAIL_RECORD_PATH,
    get_record_list,
    is_recorded,
    save_record,
)
from lib.prompt import read_email_system_prompt


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

    mail_records = get_record_list(EMAIL_RECORD_PATH)

    # Prune the email record to remove emails older than 7 days
    mail_records = prune_email_record(mail_records)

    # Check if some email is checked
    for email in emails:
        checked = is_recorded(mail_records, email["id"])

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
    llm = LLM()
    system_prompt = read_email_system_prompt()
    llm_response = llm.run_chat_completion(system_prompt, email_user_prompt)

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
        mail_records = mark_email_as_checked(mail_records, email["id"])

    # Save the email record
    save_record(EMAIL_RECORD_PATH, mail_records)

    logger.success("All emails are checked")
