import json
from datetime import datetime

from loguru import logger

from lib.api.microsoft import MicrosoftGraphAPI

ONEDRIVE_STORE_FOLDER = "Data"


def get_store(path: str) -> dict[str, str]:
    default = {}

    response = MicrosoftGraphAPI().request_drive_content(
        method="GET", path=f"{ONEDRIVE_STORE_FOLDER}/{path}"
    )

    if response.status_code == 404:
        logger.debug(f"Store file not found: {path}, returning default")
        return default

    if response.status_code >= 300:
        raise Exception(f"Error getting store file: {response.text}")

    logger.debug(f"Loaded store file: {path}")

    return response.json()


def save_store(path: str, d: dict | list):
    response = MicrosoftGraphAPI().request_drive_content(
        method="PUT",
        path=f"{ONEDRIVE_STORE_FOLDER}/{path}",
        data=json.dumps(d),
    )

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")

    logger.debug(f"Saved store file: {path}")


def get_store_with_datetime(path: str) -> dict[str, datetime]:
    d = get_store(path)
    new_data: dict[str, datetime] = {}

    for key, value in d.items():
        new_data[key] = datetime.fromisoformat(value)

    return new_data


def save_store_with_datetime(path: str, data: dict[str, datetime]):
    new_data: dict[str, str] = {}

    for key, value in data.items():
        new_data[key] = value.astimezone().isoformat()

    save_store(path, new_data)
