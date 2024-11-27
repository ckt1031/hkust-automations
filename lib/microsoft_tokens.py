import os
from datetime import datetime, timedelta, timezone

import msgspec
import requests
from loguru import logger

import lib.env as env
from lib.constant import HTTP_CLIENT_HEADERS

TMP_ACCESS_TOKEN_PATH = "./tmp/access_token.json"


class AccessTokenStore(msgspec.Struct):
    access_token: str
    refresh_token: str
    expires_in: int
    expiry_time: datetime | None = None


def write_access_token_to_file(data: AccessTokenStore):
    # Make sure the tmp directory exists
    if not os.path.exists("./tmp"):
        os.makedirs("./tmp")

    # Add expires_in seconds to the current time
    data.expiry_time = datetime.now(timezone.utc) + timedelta(seconds=data.expires_in)

    jsonString = msgspec.json.encode(data)

    with open(TMP_ACCESS_TOKEN_PATH, "wb") as f:
        f.write(jsonString)

    logger.success("Access token written to temp file")


def read_access_token_from_file() -> str | None:
    # Open the file, check if it exists
    try:
        with open(TMP_ACCESS_TOKEN_PATH, "rb") as f:
            jsonString = f.read()

        data = msgspec.json.decode(jsonString, type=AccessTokenStore)

        # Check if the token has expired
        if data.expiry_time < datetime.now(timezone.utc):
            logger.warning(
                f"Microsoft access token is about to expire, it expires in {data.expiry_time}"
            )
            return None

        logger.debug(f"Access token read from temp file, expires in {data.expiry_time}")

        return data.access_token
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

    jsonString = msgspec.json.decode(response.text, type=AccessTokenStore)

    write_access_token_to_file(jsonString)

    return jsonString.access_token
