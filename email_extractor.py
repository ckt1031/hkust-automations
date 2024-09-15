import email
import html
import imaplib
import os
from datetime import datetime, timedelta
from email.header import decode_header

import dotenv

from utils import (
    check_email_date,
    check_email_sender,
    clean_html,
    remove_css_and_scripts,
    remove_massive_space,
)

# Load environment variables from .env file
dotenv.load_dotenv()


UNEXPECTED_SENDER_TXT_PATH = "unexpected_sender.txt"


def save_sender_to_text(sender: str) -> None:
    # If os exists, write the sender to the file
    if os.path.exists(UNEXPECTED_SENDER_TXT_PATH):
        # Check if the sender is already in the file
        with open(UNEXPECTED_SENDER_TXT_PATH, "r") as f:
            lines = f.readlines()
            for line in lines:
                if sender in line:
                    return

        with open(UNEXPECTED_SENDER_TXT_PATH, "a") as f:
            # In new line
            f.write("\n" + sender)
    else:
        with open(UNEXPECTED_SENDER_TXT_PATH, "w") as f:
            f.write(sender)


class EmailExtractor:
    def __init__(self):
        self.IMAP_USERNAME = os.getenv("IMAP_USERNAME")
        self.IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
        self.IMAP_URL = os.getenv("IMAP_URL")
        self.IMAP_PORT = 993
        self.CHECK_PAST_HOURS = 24

        # Reject if self.IMAP_USERNAME, IMAP_PASSWORD, or IMAP_URL is None
        if not self.IMAP_URL or not self.IMAP_USERNAME or not self.IMAP_PASSWORD:
            raise ValueError("IMAP credentials not found in the environment variables")

        self.mail = imaplib.IMAP4_SSL(self.IMAP_URL, self.IMAP_PORT)

    def login(self):
        # Login to the server
        self.mail.login(self.IMAP_USERNAME, self.IMAP_PASSWORD)

    def fetch_emails(self):
        self.login()

        # Select the mailbox you want to fetch emails from
        # Options: "INBOX", but you can select other folders too
        self.mail.select("inbox")

        # Calculate the date string for the past 48 hours since it does not support time directly
        date_last = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")

        # Search for all emails
        status, messages = self.mail.search(None, f"SINCE {date_last}")

        # Messages is a list of email IDs
        email_ids = messages[0].split()

        return email_ids

    def extract_emails(self):
        """
        Extract emails from the inbox
        """

        # Messages is a list of email IDs
        email_ids = self.fetch_emails()

        # JSON List, Dict, or any other format
        emails = []

        # Iterate over the last 5 emails
        for email_id in email_ids[-5:]:
            # Fetch the email by ID
            status, msg_data = self.mail.fetch(email_id, "(RFC822)")

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
            if not check_email_date(msg["Date"], self.CHECK_PAST_HOURS):
                print(f"Email is older than {self.CHECK_PAST_HOURS} hours")
                continue

            # Print email headers and subject
            subject, encoding = decode_header(msg["Subject"])[0]

            if isinstance(subject, bytes):
                # Decode if it’s in byte format
                subject = subject.decode(encoding if encoding else "utf-8")

            body = ""

            # print("Date:", msg["Date"])
            if not check_email_sender(msg["From"]):
                print(f"Not from the expected sender ({msg['From']}): {subject}")
                continue

            # Check if the email is multipart, which is the case for most emails
            if msg.is_multipart():
                for part in msg.walk():
                    # Get the email body
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if (
                        "attachment" not in content_disposition
                        and content_type == "text/plain"
                    ):
                        # Fetch the plain text body
                        body = part.get_payload(decode=True).decode(
                            "utf-8", errors="replace"
                        )
                    elif (
                        "attachment" not in content_disposition
                        and content_type == "text/html"
                    ):
                        # If it's HTML, clean it
                        html_body = part.get_payload(decode=True).decode(
                            "utf-8", errors="replace"
                        )
                        cleaned_html = remove_css_and_scripts(html_body)
                        body = clean_html(cleaned_html)
                        body = html.unescape(body)
                        body = remove_massive_space(body)
            else:
                # If it's a single part email
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

            emails.append(
                {
                    "subject": subject,
                    "body": body,
                    "from": msg["From"],
                    "date": msg["Date"],
                }
            )

        # Logout from the server to end the session
        self.mail.logout()

        return emails
