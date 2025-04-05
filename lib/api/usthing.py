from functools import cache

import requests

from lib.env import getenv

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "USThing/113 CFNetwork/1568.100.1 Darwin/24.0.0",
    "Accept-Language": "en-GB,en;q=0.9",
}
MS_API_BASE_URL = "https://ms.api.usthing.xyz/v2"


@cache
def _get_access_token() -> str:
    talentID = "c917f3e2-9322-4926-9bb3-daca730413ca"
    clientID = "b4bc4b9a-7162-44c5-bb50-fe935dce1f5a"

    url = f"https://login.microsoftonline.com/{talentID}/oauth2/v2.0/token"

    MICROSOFT_REFRESH_TOKEN = getenv("USTHING_MICROSOFT_REFRESH_TOKEN", required=True)

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

    return response.json()["access_token"]


def get_me_info():
    url = "https://graph.microsoft.com/v1.0/me"

    token = _get_access_token()

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception("Error getting Microsoft user info: " + response.text)

    return response.json()


def get_username():
    me_info = get_me_info()

    return me_info["mail"].split("@")[0]


def _make_usthing_request(endpoint: str):
    username = get_username()
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}", **HEADERS}
    url = f"{MS_API_BASE_URL}{endpoint}?userName={username}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


@cache
def get_course_grades():
    return _make_usthing_request("/sis/stdt_courses")


@cache
def get_class_enrollments():
    return _make_usthing_request("/sis/stdt_class_enrl")
