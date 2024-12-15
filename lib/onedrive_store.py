import json
from datetime import datetime

import requests
from loguru import logger

from lib.env import Environment
from lib.microsoft_tokens import get_private_graph_token


def drive_api(method="GET", path="", data=None):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_private_graph_token()}",
        "Content-Type": "application/json",
    }

    response = requests.request(method, url, headers=headers, data=data, timeout=15)

    return response


def is_recorded(list: list[dict[str, datetime]], id: str):
    for item in list:
        if item.get(str(id)):
            return True

    return False


def get_store(path: str) -> dict[str, datetime]:
    default = {}

    base_folder = Environment.get("ONEDRIVE_STORE_FOLDER", "Programs/Information-Push")

    response = drive_api(method="GET", path=f"{base_folder}/{path}")

    if response.status_code >= 400:
        logger.error(
            f"Error getting store file ({response.status_code}): {response.text}"
        )
        return default

    data: dict[str, str] = response.json()

    for key, value in data.items():
        data[key] = datetime.fromisoformat(value)

    logger.debug(f"Loaded store file: {path}")

    return data


def save_store(path: str, record: dict[str, datetime]):
    d = record.copy()

    for key, value in d.items():
        if isinstance(value, datetime):
            d[key] = value.astimezone().isoformat()

    base_folder = Environment.get("ONEDRIVE_STORE_FOLDER", "Programs/Information-Push")

    response = drive_api(
        method="PUT",
        path=f"{base_folder}/{path}",
        data=json.dumps(d),
    )

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")

    logger.debug(f"Saved store file: {path}")
