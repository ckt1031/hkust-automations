from lib.api.microsoft import MicrosoftGraphAPI
from lib.utils import process_html_to_text


class EmailExtractor:
    def __init__(self):
        self.api = MicrosoftGraphAPI()

    def extract_emails(self):
        emails = []

        for email in self.api.fetch_emails():
            unique_body = process_html_to_text(email["uniqueBody"]["content"])

            # Replies to the email
            replies_body = None
            is_reply = "singleValueExtendedProperties" in email

            # If email is a reply, fetch more details
            if is_reply:
                replies = self.api.fetch_replies(email["conversationId"])

                # Remove the original email from the replies, one with the same id
                replies = [reply for reply in replies if reply["id"] != email["id"]]

                replies_body = [
                    {
                        "id": reply["id"],
                        "subject": reply["subject"].strip(),
                        "from": reply["sender"]["emailAddress"]["name"],
                        "date": reply["receivedDateTime"],
                        "body": process_html_to_text(reply["uniqueBody"]["content"]),
                    }
                    for reply in replies
                ]

            emails.append(
                {
                    "id": email["id"],
                    "subject": email["subject"].strip(),
                    "from": email["sender"]["emailAddress"]["name"],
                    "date": email["receivedDateTime"],
                    "body": unique_body.strip(),
                    "is_reply": is_reply,
                    "replies_body": replies_body,
                }
            )

        return emails
