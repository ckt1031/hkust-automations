import asyncio
from datetime import datetime

from langchain_text_splitters import (MarkdownHeaderTextSplitter,
                                      RecursiveCharacterTextSplitter)

import db
from email_extractor import EmailExtractor
from llm import LLM
from notification import send_discord
from rss import RSS


def read_email_system_prompt():
    with open("prompts/email-summarize.txt", "r") as f:
        return f.read()


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
        checked = db.is_email_checked(email["subject"], email["date"])

        if checked:
            print(f"Email with subject {email['subject']} is already checked")

            # Remove the email from the list
            emails.remove(email)
            continue

        email_user_prompt += f"\n\n\nSubject: {email['subject']}\nFrom: {email['from']}\nBody: {email['body']}"
        unchecked_email_amount += 1
    # If there are no unchecked emails, exit the program
    if unchecked_email_amount == 0:
        print("No unchecked emails found")
        exit()
    # Call the LLM model to summarize the emails
    llm = LLM()
    system_prompt = read_email_system_prompt()
    result = llm.complete(system_prompt, email_user_prompt)
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )
    result = markdown_splitter.split_text(result)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
    )
    splits = text_splitter.split_documents(result)
    for split in splits:
        send_discord(split.page_content, "HKUST Email")
    # Mark and save database after all actions to prevent missing emails if the program crashes
    for email in emails:
        db.mark_email_as_checked(email["subject"], email["date"])


if __name__ == "__main__":
    try:
        print("Starting the RSS summarizer")
        asyncio.run(RSS().check_all())
    except Exception as e:
        print(f"Error in RSS summarizer: {e}")

    print("Starting the email summarizer")

    email_summarize()
