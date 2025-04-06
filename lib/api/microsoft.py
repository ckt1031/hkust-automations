from datetime import datetime, timedelta
from functools import cache

import requests
from pytz import timezone

from lib.env import getenv


class MicrosoftGraphAPI:
    def __init__(self):
        self.ms_base_url = "https://graph.microsoft.com/v1.0"
        self.access_token = self.get_access_token()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        )

    @cache
    def get_access_token(self) -> str:
        client_id = getenv("MICROSOFT_CLIENT_ID")
        client_secret = getenv("MICROSOFT_CLIENT_SECRET")
        refresh_token = getenv("MICROSOFT_REFRESH_TOKEN")

        if not refresh_token or not client_id or not client_secret:
            raise Exception(
                "Microsoft refresh token, client ID, or client secret is not set"
            )

        MSFT_REDIRECT_URI = "http://localhost:53682"
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

        payload = {
            "grant_type": "refresh_token",
            "REDIRECT_URL": MSFT_REDIRECT_URI,
            "CLIENT_ID": client_id,
            "CLIENT_SECRET": client_secret,
            "refresh_token": refresh_token,
        }

        response = requests.post(url, data=payload, timeout=5)

        if response.status_code != 200:
            raise Exception("Error getting Microsoft access token: " + response.text)

        return response.json()["access_token"]

    def get_inbox_folder_id(self):
        url = f"{self.ms_base_url}/me/mailFolders/inbox"

        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception("Error fetching inbox folders")

        return response.json()["id"]

    def fetch_replies(self, conversation_id: str) -> list[dict]:
        url = f"{self.ms_base_url}/me/mailFolders/inbox/messages"

        params = [
            ("$top", "50"),
            ("$select", "sender,subject,receivedDateTime,uniqueBody"),
            ("$filter", f"conversationId eq '{conversation_id}'"),
        ]

        response = self.session.get(url, params=params)

        if response.status_code != 200:
            raise Exception("Error fetching email replies")

        data: list[dict] = response.json()["value"]
        data.sort(key=lambda x: x["receivedDateTime"], reverse=True)

        return data

    def fetch_emails(self) -> list[dict]:
        inbox_id = self.get_inbox_folder_id()

        url = f"{self.ms_base_url}/me/mailFolders/{inbox_id}/messages"

        date_filter_yesterday = datetime.now() - timedelta(days=3)
        date_filter_yesterday = date_filter_yesterday.replace(
            tzinfo=timezone("Asia/Hong_Kong")
        )

        params = [
            ("$top", "250"),
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

    def request_drive_content(self, method="GET", path="", data=None):
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = self.session.request(
            method,
            url,
            headers=headers,
            data=data,
            timeout=10,
        )

        return response

    def create_todo_task(
        self,
        list_id: str,  # The ID of the task list
        title: str,
        due_date: str = None,
        body: str = None,
    ) -> dict:
        """Create a new task in Microsoft To Do

        Args:
            title: Title of the task
            due_date: Due date in ISO 8601 format
            body: Optional body/description of the task

        Returns:
            dict: Created task data
        """
        url = f"{self.ms_base_url}/me/todo/lists/{list_id}/tasks"

        task_data = {"title": title, "status": "notStarted"}

        if due_date:
            task_data["dueDateTime"] = {
                "dateTime": due_date,
                "timeZone": "Asia/Hong_Kong",
            }

        if body:
            task_data["body"] = {"content": body, "contentType": "text"}

        response = self.session.post(url, json=task_data)

        if response.status_code != 201:
            raise Exception(f"Error creating task: {response.text}")

        return response.json()

    def list_tasks(self, list_id: str) -> list[dict]:
        """List all tasks in a specific list in Microsoft To Do

        Args:
            list_id: ID of the task list

        Returns:
            list[dict]: List of task dictionaries containing:
                - id: Task ID
                - title: Task title
                - status: Task status
                - dueDateTime: Due date if set
                - body: Description if set
        """
        url = f"{self.ms_base_url}/me/todo/lists/{list_id}/tasks"

        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Error listing tasks: {response.text}")

        # Simplify task data structure
        return response.json().get("value", [])

    def list_tasks_lists(self) -> list[dict]:
        """List all tasks in Microsoft To Do

        Returns:
            list[dict]: List of task dictionaries containing:
                - id: Task ID
                - title: Task title
                - status: Task status
                - dueDateTime: Due date if set
                - body: Description if set
        """
        url = f"{self.ms_base_url}/me/todo/lists"

        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Error listing tasks: {response.text}")

        # Simplify task data structure
        return response.json().get("value", [])
