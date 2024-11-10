import sys
from datetime import datetime

from langchain_text_splitters import MarkdownHeaderTextSplitter
from loguru import logger

from email_summarizer.email_extractor import EmailExtractor
from email_summarizer.email_record import is_email_checked, mark_email_as_checked
from lib.llm import LLM
from lib.notification import send_discord
from lib.onedrive_store import get_email_record, save_email_record
from lib.prompt import read_email_system_prompt

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")


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

    mail_records = get_email_record()

    # Check if some email is checked
    for email in emails:
        checked = is_email_checked(mail_records, email["id"])

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

    for split in result:
        send_discord(split.page_content, "HKUST Email")

    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in emails:
        mark_email_as_checked(mail_records, email["id"])

    # Save the email record
    save_email_record(mail_records)

    logger.success("All emails are checked")


if __name__ == "__main__":
    logger.info("Starting the email summarizer")

    email_summarize()
