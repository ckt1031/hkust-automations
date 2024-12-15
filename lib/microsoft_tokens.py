import json
import os
from datetime import datetime, timedelta, timezone

import requests
from loguru import logger

from lib.env import Environment

TMP_FOLDER = "./tmp"
TMP_ACCESS_TOKEN_PATH = f"{TMP_FOLDER}/access_token.json"


def write_access_token_to_file(data: dict):
    # Make sure the tmp directory exists
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)

    # Add expires_in seconds to the current time
    data["expiry_time"] = (
        datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    ).isoformat()

    with open(TMP_ACCESS_TOKEN_PATH, "w") as f:
        f.write(json.dumps(data, indent=4))

    logger.success("Access token written to temp file")


def read_access_token_from_file() -> str | None:
    # Open the file, check if it exists
    try:
        with open(TMP_ACCESS_TOKEN_PATH, "r") as f:
            jsonString = f.read()

        if not jsonString or jsonString == "":
            return None

        data: dict = json.loads(jsonString)
        expiry_time = datetime.fromisoformat(data["expiry_time"])

        # Check if the token has expired
        if expiry_time < datetime.now(timezone.utc):
            logger.warning(
                f"Microsoft access token is about to expire, it expires in {data['expiry_time']}"
            )
            return None

        logger.debug(
            f"Access token read from temp file, expires in {data['expiry_time']}"
        )

        return data["access_token"]
    except FileNotFoundError:
        return None


def get_private_graph_token():
    access_token = read_access_token_from_file()

    if access_token:
        return access_token

    refresh_token = Environment.get("MICROSOFT_REFRESH_TOKEN")
    client_id = Environment.get("MICROSOFT_CLIENT_ID")
    client_secret = Environment.get("MICROSOFT_CLIENT_SECRET")

    if not refresh_token or not client_id or not client_secret:
        logger.error("Microsoft refresh token, client ID, or client secret is not set")
        return

    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    payload = {
        "grant_type": "refresh_token",
        "REDIRECT_URL": "https://login.microsoftonline.com/common/oauth2/nativeclient",
        "CLIENT_ID": client_id,
        "CLIENT_SECRET": client_secret,
        "refresh_token": refresh_token,
    }

    response = requests.post(url, data=payload, timeout=15)

    if response.status_code != 200:
        logger.error(
            f"Error getting microsoft access token ({response.status_code}): {response.text}"
        )
        return None

    data: dict = response.json()

    # Write the access token to a file
    write_access_token_to_file(data)

    return data["access_token"]
