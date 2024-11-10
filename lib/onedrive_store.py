import json
import os

import requests

from lib.microsoft_tokens import get_private_graph_token

EMAIL_RECORD_FOLDER = os.getenv("ONEDRIVE_STORE_FOLDER", "Programs/Information-Push")
EMAIL_RECORD_PATH = f"{EMAIL_RECORD_FOLDER}/email_record.json"


def drive_api(method="GET", path="", data=None):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/content"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_private_graph_token()}",
        "Content-Type": "application/json",
    }

    response = requests.request(method, url, headers=headers, data=data)

    return response


def get_email_record() -> list[dict[str, str]]:
    default = []

    response = drive_api(path=EMAIL_RECORD_PATH)

    if response.status_code != 200:
        print(f"Error getting email record: {response.text}")
        return default

    return response.json()


def save_email_record(email_record: list[dict[str, str]]):
    json_data = json.dumps(email_record)

    response = drive_api(method="PUT", path=EMAIL_RECORD_PATH, data=json_data)

    if response.status_code >= 300:
        raise Exception(f"Error uploading store file: {response.text}")
