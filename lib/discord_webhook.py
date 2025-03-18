from datetime import datetime, timedelta
from time import sleep

import requests
from cachetools import TTLCache
from loguru import logger

cache = TTLCache(maxsize=10, ttl=60)


def get_cooldown_status():
    return {
        "required": cache.get("required", False),
        "expiry": cache.get("expiry", datetime.now()),
    }


def set_cooldown_status(required: bool, expiry: datetime):
    cache["required"] = required
    cache["expiry"] = expiry


def send_discord_webhook(
    webhook_url: str,
    message: str | None = None,
    embed: dict | None = None,
    username="School",
):
    now = datetime.now()
    status = get_cooldown_status()

    if status["required"] and (status["expiry"] > now):
        seconds_left: timedelta = status["expiry"] - now
        seconds_left = seconds_left.total_seconds()

        logger.debug(f"Discord ratelimit reached, sleeping for {seconds_left}s")

        # Sleep for the remaining cooldown time
        sleep(seconds_left)

        # Reset the cooldown status
        set_cooldown_status(False, datetime.now())

    data = {"content": message, "username": username}

    if embed is not None:
        data["embeds"] = [embed]

    # Send the message to the Discord webhook
    response = requests.post(webhook_url, json=data)

    if response.status_code != 204:
        raise ValueError(
            f"Discord webhook request failed {response.status_code}",
            response.text,
        )

    # Check X-RateLimit-Limit and X-RateLimit-Remaining headers
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_after = response.headers.get("X-RateLimit-Reset-After")

    if remaining is None or reset_after is None:
        return

    if int(remaining) == 1:
        expiry = now + timedelta(seconds=float(reset_after))
        set_cooldown_status(required=True, expiry=expiry)
