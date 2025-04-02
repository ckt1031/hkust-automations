from datetime import datetime, timedelta

import requests
from pytz import timezone

from lib.microsoft_tokens import get_own_app_private_graph_token


class MicrosoftGraphAPI:
    def __init__(self):
        self.ms_base_url = "https://graph.microsoft.com/v1.0"
        self.access_token = get_own_app_private_graph_token()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        )

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
            ("$filter", f"conversationId eq '{conversation_id}'"),
        ]

        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise Exception("Error fetching email replies")

        data: list[dict] = response.json()["value"]
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
            (
                "$expand",
                "SingleValueExtendedProperties($filter=(Id eq 'String 0x1042'))",
            ),
        ]

        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise Exception("Error fetching emails")

        return response.json()["value"]
