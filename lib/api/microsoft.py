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
