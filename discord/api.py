import base64

import requests

from lib.env import Environment

DISCORD_API_BASE_URL = "https://discord.com/api/v10"


def get_discord_headers(ref: str):
    headers = {
        "Authorization": Environment.get("DISCORD_USER_TOKEN"),
        # Mock browser headers
        "Host": "discord.com",
        "Priority": "undefined",
        "Accept": "u=3, i",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
        "Connection": "keep-alive",
        "Referer": ref,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Debug-Options": "bugReporterEnabled",
        "X-Discord-Locale": "en-US",
        "X-Discord-Timezone": "Asia/Hong_Kong",
    }

    DISCORD_INFO = {
        "os": "Mac OS X",
        "browser": "Safari",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": headers["User-Agent"],
        "browser_version": "18.1.1",
        "os_version": "10.15.7",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": 347699,
        "client_event_source": None,
    }

    headers["X-Super-Properties"] = base64.b64encode(
        str(DISCORD_INFO).encode("utf-8")
    ).decode("utf-8")

    return headers


def get_channel_info(server_id: str, channel_id: str) -> dict:
    headers = get_discord_headers(
        f"https://discord.com/channels/{server_id}/{channel_id}"
    )

    url = f"{DISCORD_API_BASE_URL}/channels/{channel_id}"

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception(f"Failed to get channel info: {response.text}")

    return response.json()


def get_channel_messages(
    server_id: str, channel_id: str, limit=None, around=None
) -> list:
    headers = get_discord_headers(
        f"https://discord.com/channels/{server_id}/{channel_id}"
    )

    url = f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages"

    params = {}

    if limit:
        params["limit"] = limit

    if around:
        params["around"] = around

    response = requests.get(url, params=params, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception(f"Failed to get channel messages: {response.text}")

    return response.json()
