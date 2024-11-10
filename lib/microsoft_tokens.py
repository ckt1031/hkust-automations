import json

import requests
from rich.console import Console

import lib.env as env

console = Console()


def get_private_graph_token():
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

    return json.loads(response.text)["access_token"]
