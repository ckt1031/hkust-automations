import json
import os
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger

import lib.env as env
from lib.constant import HTTP_CLIENT_HEADERS

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

    if (
        not env.MICROSOFT_REFRESH_TOKEN
        or not env.MICROSOFT_CLIENT_ID
        or not env.MICROSOFT_CLIENT_SECRET
    ):
        logger.error("Microsoft refresh token, client ID, or client secret is not set")
        return

    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    payload = {
        "grant_type": "refresh_token",
        "REDIRECT_URL": "https://login.microsoftonline.com/common/oauth2/nativeclient",
        "CLIENT_ID": env.MICROSOFT_CLIENT_ID,
        "CLIENT_SECRET": env.MICROSOFT_CLIENT_SECRET,
        "refresh_token": env.MICROSOFT_REFRESH_TOKEN,
    }

    client = httpx.Client(headers=HTTP_CLIENT_HEADERS, timeout=15, http2=True)
    response = client.post(url, data=payload)

    if response.status_code != 200:
        logger.error(
            f"Error getting microsoft access token ({response.status_code}): {response.text}"
        )
        return None

    data: dict = response.json()

    # Write the access token to a file
    write_access_token_to_file(data)

    return data["access_token"]
