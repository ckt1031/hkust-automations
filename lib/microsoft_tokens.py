import json
import os
from datetime import datetime, timedelta, timezone

import requests
from loguru import logger

import lib.env as env
from lib.constant import HTTP_CLIENT_HEADERS
from lib.utils import iso_time_from_now_second_left

TMP_ACCESS_TOKEN_PATH = "./tmp/access_token.json"


def write_access_token_to_file(jsonString: str):
    # Make sure the tmp directory exists
    if not os.path.exists("./tmp"):
        os.makedirs("./tmp")

    data = json.loads(jsonString)

    swifted_time = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])

    # Add expires_in seconds to the current time
    data["expiry_time"] = swifted_time.isoformat()

    jsonString = json.dumps(data)

    with open(TMP_ACCESS_TOKEN_PATH, "w") as f:
        f.write(jsonString)

    logger.success("Access token written to temp file")


def read_access_token_from_file() -> str | None:
    # Open the file, check if it exists
    try:
        with open(TMP_ACCESS_TOKEN_PATH, "r") as f:
            jsonString = f.read()

        data = json.loads(jsonString)

        # Check if the token has expired
        if iso_time_from_now_second_left(data["expiry_time"]) < 120:
            logger.warning(
                f"Microsoft access token is about to expire, it expires in {data['expiry_time']}"
            )
            return None

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

    response = requests.post(url, data=payload, headers=HTTP_CLIENT_HEADERS)

    if response.status_code != 200:
        logger.error(
            f"Error getting microsoft access token ({response.status_code}): {response.text}"
        )
        return None

    jsonString = response.text

    write_access_token_to_file(jsonString)

    return json.loads(jsonString)["access_token"]
