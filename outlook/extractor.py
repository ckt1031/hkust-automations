import re
import string

import html2text
import requests
from loguru import logger

from lib.microsoft_tokens import get_private_graph_token
from lib.utils import remove_css_and_scripts


def remove_non_ascii(text: str):
    printable = set(string.printable)
    text = "".join(filter(lambda x: x in printable, text))

    return text.encode("ascii", errors="ignore").decode()


def remove_excessive_newlines(text: str):
    return text.replace("\n\n", "\n").replace("\n\n", "\n")


# Keep newlines, but remove excessive spaces
def remove_excessive_spaces(text: str):
    return re.sub(r"[ \t]+", " ", text)


class EmailExtractor:
    def __init__(self):
        self.access_token = get_private_graph_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        self.session = requests.Session()
        self.session.headers.update(headers)

    def get_inbox_folder_id(self):
        url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox"

        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception("Error fetching inbox folders")

        return response.json()["id"]

    def fetch_emails(self):
        inbox_id = self.get_inbox_folder_id()

        url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{inbox_id}/messages?$select=sender,subject,body,receivedDateTime"

        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception("Error fetching emails")

        return response.json()["value"]

    def extract_emails(self):
        emails = []

        for email in self.fetch_emails():
            txt = html2text.HTML2Text()
            txt.ignore_emphasis = True
            txt.ignore_images = True

            body = txt.handle(email["body"]["content"])
            body = remove_css_and_scripts(body)
            body = remove_excessive_newlines(body)
            body = remove_excessive_spaces(body)

            emails.append(
                {
                    "id": email["id"],
                    "subject": email["subject"].strip(),
                    "body": body,
                    "from": email["sender"]["emailAddress"]["name"],
                    "date": email["receivedDateTime"],
                }
            )

        return emails
