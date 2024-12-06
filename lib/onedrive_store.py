import json
from datetime import datetime

import httpx
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

client = httpx.Client(timeout=15, http2=True, headers=HTTP_CLIENT_HEADERS)


def drive_api(method="GET", path="", data=None):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_private_graph_token()}",
        "Content-Type": "application/json",
    }

    response = client.request(method, url, headers=headers, data=data)

    return response


def is_recorded(list: list[dict[str, datetime]], id: str):
    for item in list:
        if item.get(str(id)):
            return True

    return False


def get_store(path: str) -> dict[str, datetime]:
    default = {}

    response = drive_api(method="GET", path=path)

    if response.status_code >= 400:
        logger.error(
            f"Error getting store file ({response.status_code}): {response.text}"
        )
        return default

    # Get location of the file
    location = response.headers.get("Location")

    if location:
        response = client.get(location)

        if response.status_code >= 300:
            logger.error(
                f"Error getting store file ({response.status_code}): {response.text}"
            )
            return default

        data: dict[str, str] = response.json()

        for key, value in data.items():
            data[key] = datetime.fromisoformat(value)

        logger.debug(f"Loaded store file: {path}")

        return data

    return default


def save_store(path: str, record: dict[str, datetime]):
    d = record.copy()

    for key, value in d.items():
        if isinstance(value, datetime):
            d[key] = value.astimezone().isoformat()

    response = drive_api(
        method="PUT",
        path=path,
        data=json.dumps(d),
    )

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")

    logger.debug(f"Saved store file: {path}")
