import sys
from datetime import datetime

from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

import lib.db as db
from email_summarizer.email_extractor import EmailExtractor
from lib.llm import LLM
from lib.notification import send_discord

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")


def read_email_system_prompt():
    with open("prompts/email-summarize.txt", "r") as f:
        return f.read()


def mark_email_as_checked(email_subject: str, date: str):
    key = db.hash_string_sha256(f"{email_subject} - {db.get_ms(date)}")
    expiring_time_in_seconds = 60 * 60 * 24 * 3  # 3 days
    db.set_redis_boolean_value(key, True, expiring_time_in_seconds)


def is_email_checked(email_subject: str, date: str):
    # Hash the email subject
    key = db.hash_string_sha256(f"{email_subject} - {db.get_ms(date)}")

    return db.is_record_exist(key)


def email_summarize():
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

    # Check if some email is checked
    for email in emails:
        checked = is_email_checked(email["subject"], email["date"])

        if checked:
            logger.info(f"Email with subject \"{email['subject']}\" is already checked")

            # Remove the email from the list
            emails.remove(email)
            continue

        email_user_prompt += f"\n\n\nSubject: {email['subject']}\nFrom: {email['from']}\nBody: {email['body']}"
        unchecked_email_amount += 1

    # If there are no unchecked emails, exit the program
    if unchecked_email_amount == 0:
        logger.success("No unchecked emails found")
        sys.exit(0)

    # Call the LLM model to summarize the emails
    llm = LLM()
    system_prompt = read_email_system_prompt()
    llm_response = llm.complete(system_prompt, email_user_prompt)

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )
    result = markdown_splitter.split_text(llm_response)

    # text_splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=1024,
    # )
    # splits = text_splitter.split_documents(result)

    for split in result:
        send_discord(split.page_content, "HKUST Email")
    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in emails:
        mark_email_as_checked(email["subject"], email["date"])

    logger.success("All emails are checked")


if __name__ == "__main__":
    logger.info("Starting the email summarizer")

    email_summarize()
