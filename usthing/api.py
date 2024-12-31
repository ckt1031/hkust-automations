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


@cache
def get_course_grades():
    username = get_username()
    token = get_usthing_private_graph_token()
    url = f"{MS_API_BASE_URL}/sis/stdt_courses?userName={username}"
    res = requests.get(
        url, headers={"Authorization": f"Bearer {token}", **HEADERS}, timeout=10
    )
    return res.json()


@cache
def get_class_enrollments():
    username = get_username()
    token = get_usthing_private_graph_token()
    url = f"{MS_API_BASE_URL}/sis/stdt_class_enrl?userName={username}"
    res = requests.get(
        url, headers={"Authorization": f"Bearer {token}", **HEADERS}, timeout=10
    )
    return res.json()
