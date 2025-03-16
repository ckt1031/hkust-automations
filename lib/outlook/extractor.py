import re
import urllib.parse
from datetime import datetime, timedelta

import html2text
import requests
from loguru import logger
from pytz import timezone

from lib.microsoft_tokens import get_own_app_private_graph_token


def remove_excessive_new_lines(text: str) -> str:
    return "\n".join([line for line in text.split("\n") if line.strip()])


def convert_safelinks_from_text(text: str) -> str:
    """
    Converts Safe Links URLs found within a plain text string to their original URLs.

    Args:
        text: The input text string potentially containing Safe Links URLs.

    Returns:
        The text string with Safe Links URLs replaced by their original URLs.
        If a Safe Link cannot be decoded, it is left unchanged.
    """

    def decode_safe_link(safe_link_url):
        """Decodes a single Safe Links URL."""
        try:
            parsed_url = urllib.parse.urlparse(safe_link_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            original_url = query_params.get("url", [None])[0]  # Get the 'url' parameter
            return original_url
        except Exception as e:
            logger.debug(f"Error decoding URL: {safe_link_url} - {e}")

            return safe_link_url  # Return the original if decoding fails

    # Regular expression to match Safe Links URLs.  This is improved for robustness.
    safe_link_pattern = r"(https?://[^\s]*safelinks\.protection\.outlook\.com[^\s]*)"

    def replace_safe_link(match):
        """
        Callback function for re.sub.  Decodes the matched Safe Link and returns
        the original URL or the Safe Link if decoding fails.
        """
        safe_link = match.group(1)
        decoded_url = decode_safe_link(safe_link)
        return decoded_url if decoded_url else safe_link

    # Use re.sub to find all Safe Links and replace them with the decoded URLs.
    processed_text = re.sub(safe_link_pattern, replace_safe_link, text)
    return processed_text


def process_html_to_text(html: str) -> str:
    txt = html2text.HTML2Text(bodywidth=0)
    txt.ignore_emphasis = True
    txt.ignore_images = True

    final_text = txt.handle(html)
    final_text = remove_excessive_new_lines(final_text)
    final_text = convert_safelinks_from_text(final_text)

    return final_text


class EmailExtractor:
    def __init__(self):
        self.ms_base_url = "https://graph.microsoft.com/v1.0"
        self.access_token = get_own_app_private_graph_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        self.session = requests.Session()
        self.session.headers.update(headers)

    def get_inbox_folder_id(self):
        url = f"{self.ms_base_url}/me/mailFolders/inbox"

        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception("Error fetching inbox folders")

        return response.json()["id"]

    def fetch_replies(self, conversation_id):
        url = f"{self.ms_base_url}/me/mailFolders/inbox/messages"

        params = [
            ("$top", "500"),
            ("$select", "sender,subject,receivedDateTime,uniqueBody"),
            # ("$orderby", "receivedDateTime desc"), # Causes error due to complex query
            ("$filter", f"conversationId eq '{conversation_id}'"),
        ]

        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise Exception("Error fetching email replies")

        data: list[dict] = response.json()["value"]

        # Reorder the receivedDateTime (ISO) in des order
        data.sort(key=lambda x: x["receivedDateTime"], reverse=True)

        return data

    def fetch_emails(self):
        inbox_id = self.get_inbox_folder_id()

        url = f"{self.ms_base_url}/me/mailFolders/{inbox_id}/messages"

        date_filter_yesterday = datetime.now() - timedelta(days=1)
        date_filter_yesterday = date_filter_yesterday.replace(
            tzinfo=timezone("Asia/Hong_Kong")
        )

        params = [
            ("$top", "500"),
            ("$select", "sender,subject,receivedDateTime,uniqueBody,conversationId"),
            ("$orderby", "receivedDateTime desc"),
            ("$filter", f"receivedDateTime ge {date_filter_yesterday.isoformat()}"),
            # Add property to check if email is a reply
            (
                "$expand",
                "SingleValueExtendedProperties($filter=(Id eq 'String 0x1042'))",
            ),
        ]

        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise Exception("Error fetching emails")

        return response.json()["value"]

    def extract_emails(self):
        emails = []

        for email in self.fetch_emails():
            is_reply = "singleValueExtendedProperties" in email
            replies_body = []
            unique_body = process_html_to_text(email["uniqueBody"]["content"])

            # If email is a reply, fetch more details
            if is_reply:
                replies = self.fetch_replies(email["conversationId"])

                # Remove the original email from the replies, one with the same id
                replies = [reply for reply in replies if reply["id"] != email["id"]]
                for reply in replies:
                    replies_body.append(
                        {
                            "date": reply["receivedDateTime"],
                            "body": process_html_to_text(
                                reply["uniqueBody"]["content"]
                            ),
                        }
                    )

            emails.append(
                {
                    "id": email["id"],
                    "subject": email["subject"].strip(),
                    "from": email["sender"]["emailAddress"]["name"],
                    "date": email["receivedDateTime"],
                    "body": unique_body,
                    "is_reply": is_reply,
                    "replies_body": replies_body,
                }
            )

        return emails
