import httpx
from loguru import logger

from email_summarizer.store import check_email_sender
from lib.constant import HTTP_CLIENT_HEADERS
from lib.microsoft_tokens import get_private_graph_token
from lib.utils import clean_html, remove_css_and_scripts


class EmailExtractor:
    def __init__(self):
        self.access_token = get_private_graph_token()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": HTTP_CLIENT_HEADERS["User-Agent"],
        }
        self.session = httpx.Client(http2=True, headers=headers)

    def fetch_emails(self):
        url = "https://graph.microsoft.com/v1.0/me/messages?$select=sender,subject,body,receivedDateTime"

        response = self.session.get(url)

        if response.status_code != 200:
            logger.error("Error fetching emails")
            return []

        return response.json()["value"]

    def extract_emails(self):
        emails = []

        for email in self.fetch_emails():
            send_address = email["sender"]["emailAddress"]["address"]

            if not check_email_sender(send_address):
                logger.info(
                    f"Not from the expected sender ({send_address}): {email['subject']}"
                )
                continue

            body = remove_css_and_scripts(clean_html(email["body"]["content"]))
            body = body.strip()

            emails.append(
                {
                    "id": email["id"],
                    "subject": email["subject"],
                    "body": body,
                    "from": email["sender"]["emailAddress"]["name"],
                    "date": email["receivedDateTime"],
                }
            )

        return emails
