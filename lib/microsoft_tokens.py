import json
import os
from datetime import datetime, timedelta, timezone

import requests
from rich.console import Console

import lib.env as env

console = Console()

TMP_ACCESS_TOKEN_PATH = "./tmp/access_token.json"


def write_access_token_to_file(jsonString: str):
    # Make sure the tmp directory exists

    if not os.path.exists("./tmp"):
        os.makedirs("./tmp")

    data = json.loads(jsonString)

    # Add expires_in seconds to the current time
    data["expiry_time"] = (
        datetime.now(timezone.utc).astimezone() + timedelta(seconds=data["expires_in"])
    ).isoformat()

    jsonString = json.dumps(data)

    with open(TMP_ACCESS_TOKEN_PATH, "w") as f:
        f.write(jsonString)


def read_access_token_from_file() -> str | None:
    # Open the file, check if it exists
    try:
        with open(TMP_ACCESS_TOKEN_PATH, "r") as f:
            jsonString = f.read()

        data = json.loads(jsonString)

        # Check if the token has expired
        expiry_time = datetime.fromisoformat(data["expiry_time"])

        # If the token has expired, return None
        if (datetime.now(timezone.utc).astimezone() - expiry_time).seconds > 0:
            return None

        return data["access_token"]
    except FileNotFoundError:
        return None


def get_private_graph_token():
    access_token = read_access_token_from_file()

    if access_token:
        return access_token

    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    payload = {
        "grant_type": "refresh_token",
        "REDIRECT_URL": "https://login.microsoftonline.com/common/oauth2/nativeclient",
        "CLIENT_ID": env.MICROSOFT_CLIENT_ID,
        "CLIENT_SECRET": env.MICROSOFT_CLIENT_SECRET,
        "refresh_token": env.MICROSOFT_REFRESH_TOKEN,
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        console.print(f"Error: {response.text}")
        return None

    jsonString = response.text

    write_access_token_to_file(jsonString)

    return json.loads(jsonString)["access_token"]
