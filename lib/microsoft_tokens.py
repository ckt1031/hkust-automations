from functools import cache

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed

from lib.env import getenv

TMP_FOLDER = "./tmp"


@cache
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_me_info(token: str):
    url = "https://graph.microsoft.com/v1.0/me"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception("Error getting Microsoft user info: " + response.text)

    return response.json()


@cache
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_private_graph_token():
    client_id = getenv("MICROSOFT_CLIENT_ID")
    client_secret = getenv("MICROSOFT_CLIENT_SECRET")
    refresh_token = getenv("MICROSOFT_REFRESH_TOKEN")

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
        raise Exception("Error getting Microsoft access token: " + response.text)

    data: dict = response.json()

    return data["access_token"]


@cache
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_usthing_private_graph_token():
    talentID = "c917f3e2-9322-4926-9bb3-daca730413ca"
    clientID = "b4bc4b9a-7162-44c5-bb50-fe935dce1f5a"

    url = f"https://login.microsoftonline.com/{talentID}/oauth2/v2.0/token"

    MICROSOFT_REFRESH_TOKEN = getenv("USTHING_MICROSOFT_REFRESH_TOKEN")

    payload = {
        "client_id": clientID,
        "grant_type": "refresh_token",
        "redirect_uri": "usthing://oauth-login",
        "refresh_token": MICROSOFT_REFRESH_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=5)

    if response.status_code != 200:
        raise Exception(
            "Error getting USTHing Microsoft access token: " + response.text
        )

    data: dict = response.json()

    return data["access_token"]
