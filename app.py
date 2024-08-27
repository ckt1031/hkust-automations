import email
import imaplib
import os
from datetime import datetime, timedelta
from email.header import decode_header

import dotenv

from utils import (check_email_date, check_email_sender, clean_html,
                   get_sender_email, remove_css_and_scripts)

# Load environment variables from .env file
dotenv.load_dotenv()

# Access environment variables
IMAP_USERNAME = os.getenv("IMAP_USERNAME")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
IMAP_URL = os.getenv("IMAP_URL")
IMAP_PORT = 993

# Configurations
CHECK_PAST_HOURS = 12

# Create an IMAP session
mail = imaplib.IMAP4_SSL(IMAP_URL, IMAP_PORT)

# Login to the server
mail.login(IMAP_USERNAME, IMAP_PASSWORD)

# Select the mailbox you want to fetch emails from
# Options: "INBOX", but you can select other folders too
mail.select("inbox")

# Calculate the date string for the past 48 hours since it does not support time directly
date_last = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")

# Search for all emails
status, messages = mail.search(None, f"SINCE {date_last}")

# Messages is a list of email IDs
email_ids = messages[0].split()


# Iterate over the last 5 emails
for email_id in email_ids[-5:]:
    # Fetch the email by ID
    status, msg_data = mail.fetch(email_id, "(RFC822)")

    # Check if the email is properly fetched
    if status != "OK":
        print("Error fetching the email", email_id)
        continue

    if msg_data[0] is None:
        print("No email data found", email_id)
        continue

    data: tuple = msg_data[0]

    # msg_data contains the raw email data
    raw_email = data[1]

    # Parse the email raw data into a message object
    msg = email.message_from_bytes(raw_email)

    # Continue if email is older than EARLIEST_DATE
    if not check_email_date(msg["Date"], CHECK_PAST_HOURS):
        print(f"Email is older than {CHECK_PAST_HOURS} hours")
        continue

    # Print email headers and subject
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        # Decode if it’s in byte format
        subject = subject.decode(encoding if encoding else "utf-8")

    body = ""

    # Check

    # print("Date:", msg["Date"])
    if not check_email_sender(msg["From"]):
        print(f"Not from the expected sender ({msg['From']})")
        continue

    # Check if the email is multipart, which is the case for most emails
    if msg.is_multipart():
        for part in msg.walk():
            # Get the email body
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition and content_type == "text/plain":
                # Fetch the plain text body
                body = part.get_payload(decode=True).decode("utf-8")
            elif (
                "attachment" not in content_disposition and content_type == "text/html"
            ):
                # If it's HTML, clean it
                html_body = part.get_payload(decode=True).decode("utf-8")
                cleaned_html = remove_css_and_scripts(html_body)
                body = clean_html(cleaned_html)
    else:
        # If it's a single part email
        body = msg.get_payload(decode=True).decode("utf-8")

    # Print the cleaned body
    print("Body:", body)

# Logout from the server to end the session
mail.logout()
