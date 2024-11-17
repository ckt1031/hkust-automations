import json

import requests

from lib import env
from lib.microsoft_tokens import get_private_graph_token

STORE_FOLDER = env.ONEDRIVE_STORE_FOLDER
EMAIL_RECORD_PATH = f"{STORE_FOLDER}/email_record.json"
CANVAS_ASSIGNMENT_REMINDER_PATH = f"{STORE_FOLDER}/canvas_assignment_reminder.json"
CANVAS_INBOX_REMINDER_PATH = f"{STORE_FOLDER}/canvas_inbox_reminder.json"


def drive_api(method="GET", path="", data=None):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_private_graph_token()}",
        "Content-Type": "application/json",
    }

    response = requests.request(method, url, headers=headers, data=data)

    return response


def get_record(path: str) -> list[dict[str, str]]:
    default = []

    response = drive_api(method="GET", path=path)

    if response.status_code != 200:
        print(f"Error getting store file: {response.text}")
        return default

    return response.json()


def save_record(path: str, record: list[dict[str, str]]):
    json_data = json.dumps(record)

    response = drive_api(method="PUT", path=path, data=json_data)

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")
