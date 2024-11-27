from datetime import datetime

import msgspec
import requests
from loguru import logger

from lib import env
from lib.constant import HTTP_CLIENT_HEADERS
from lib.microsoft_tokens import get_private_graph_token

STORE_FOLDER = env.ONEDRIVE_STORE_FOLDER

# Stores
EMAIL_RECORD_PATH = f"{STORE_FOLDER}/email_record.json"
RSS_NEWS_RECORD_PATH = f"{STORE_FOLDER}/rss_news_record.json"

CANVAS_INBOX_REMINDER_PATH = f"{STORE_FOLDER}/canvas_inbox_reminder.json"
CANVAS_ANNOUNCEMENT_RECORD_PATH = f"{STORE_FOLDER}/canvas_announcement_record.json"
CANVAS_ASSIGNMENT_REMINDER_PATH = f"{STORE_FOLDER}/canvas_assignment_reminder.json"

DISCORD_CHANNEL_SUMMARY_PATH = f"{STORE_FOLDER}/discord_channel_summary.json"


def drive_api(method="GET", path="", data=None):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_private_graph_token()}",
        "Content-Type": "application/json",
        "User-Agent": HTTP_CLIENT_HEADERS["User-Agent"],
    }

    response = requests.request(method, url, headers=headers, data=data)

    return response


def is_recorded(list: list[dict[str, datetime]], id: str):
    for item in list:
        if item.get(str(id)):
            return True

    return False


def get_record_list(path: str) -> list[dict[str, datetime]]:
    default = []

    response = drive_api(method="GET", path=path)

    if response.status_code != 200:
        logger.error(f"Error getting store file: {response.text}")
        return default

    return msgspec.json.decode(response.text, type=list[dict[str, datetime]])


def get_record_dict(path: str) -> dict[str, datetime]:
    default = {}

    response = drive_api(method="GET", path=path)

    if response.status_code != 200:
        logger.error(f"Error getting store file: {response.text}")
        return default

    return msgspec.json.decode(response.text, type=dict[str, datetime])


def save_record(path: str, record):
    json_data = msgspec.json.encode(record)

    response = drive_api(method="PUT", path=path, data=json_data)

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")
