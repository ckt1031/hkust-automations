from datetime import datetime, timedelta
from time import sleep

import httpx
from loguru import logger

from lib.constant import HTTP_CLIENT_HEADERS

COOLDOWN_REQUIRED = False
REMAINING_EXPIRY = datetime.now()
webhook_client = httpx.Client(http2=True, headers=HTTP_CLIENT_HEADERS)


def send_discord(
    webhook_url: str,
    message: str | None,
    embed: dict | None,
    username: str | None = "School",
):
    global COOLDOWN_REQUIRED, REMAINING_EXPIRY

    if COOLDOWN_REQUIRED and REMAINING_EXPIRY > datetime.now():
        seconds_left = (REMAINING_EXPIRY - datetime.now()).total_seconds()

        logger.debug(
            f"Discord webhook rate limit reached, sleeping for {seconds_left}s"
        )

        sleep(seconds_left)

        COOLDOWN_REQUIRED = False

    data = {"content": message, "username": username}

    if embed is not None:
        data["embeds"] = [embed]

    # Send the message to the Discord webhook
    response = webhook_client.post(webhook_url, json=data)

    if response.status_code != 204:
        raise ValueError(f"Discord webhook returned status code {response.status_code}")

    # Check X-RateLimit-Limit and X-RateLimit-Remaining headers
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_after = response.headers.get("X-RateLimit-Reset-After")

    if remaining is None or reset_after is None:
        return

    REMAINING = int(remaining)

    if REMAINING == 1:
        COOLDOWN_REQUIRED = True
        REMAINING_EXPIRY = datetime.now() + timedelta(seconds=float(reset_after))
