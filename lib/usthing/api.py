from functools import cache

import requests

from lib.microsoft_tokens import get_me_info, get_usthing_private_graph_token

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "USThing/113 CFNetwork/1568.100.1 Darwin/24.0.0",
    "Accept-Language": "en-GB,en;q=0.9",
}
MS_API_BASE_URL = "https://ms.api.usthing.xyz/v2"


def get_username():
    token = get_usthing_private_graph_token()
    me_info = get_me_info(token)

    return me_info["mail"].split("@")[0]


def _make_usthing_request(endpoint: str):
    username = get_username()
    token = get_usthing_private_graph_token()
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
