import json

import requests
from loguru import logger

from lib import env
from lib.microsoft_tokens import get_private_graph_token

STORE_FOLDER = env.ONEDRIVE_STORE_FOLDER

# Stores
EMAIL_RECORD_PATH = f"{STORE_FOLDER}/email_record.json"
CANVAS_ANNOUNCEMENT_RECORD_PATH = f"{STORE_FOLDER}/canvas_announcement_record.json"
CANVAS_ASSIGNMENT_REMINDER_PATH = f"{STORE_FOLDER}/canvas_assignment_reminder.json"
CANVAS_INBOX_REMINDER_PATH = f"{STORE_FOLDER}/canvas_inbox_reminder.json"
RSS_NEWS_RECORD_PATH = f"{STORE_FOLDER}/rss_news_record.json"


def drive_api(method="GET", path="", data=None):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_private_graph_token()}",
        "Content-Type": "application/json",
    }

    response = requests.request(method, url, headers=headers, data=data)

    return response


def is_recorded(list: list[dict[str, str]], id: str):
    for item in list:
        if item.get(id):
            return True

    return False


def get_record(path: str) -> list[dict[str, str]]:
    default = []

    response = drive_api(method="GET", path=path)

    if response.status_code != 200:
        logger.error(f"Error getting store file: {response.text}")
        return default

    return response.json()


def save_record(path: str, record: list[dict[str, str]]):
    json_data = json.dumps(record)

    response = drive_api(method="PUT", path=path, data=json_data)

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")
