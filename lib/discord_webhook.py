from datetime import datetime, timedelta
from time import sleep

import requests
from cachetools import TTLCache
from loguru import logger

cache = TTLCache(maxsize=10, ttl=60)


def get_cooldown_status():
    expiry = cache.get("remaining_expiry", datetime.now().isoformat())
    expiry = datetime.fromisoformat(expiry)

    data = {
        "cooldown_required": cache.get("cooldown_required", False),
        "remaining_expiry": expiry,
    }

    return data


def set_cooldown_status(cooldown_required: bool, remaining_expiry: datetime):
    cache["cooldown_required"] = cooldown_required
    cache["remaining_expiry"] = remaining_expiry.isoformat()


def send_discord_webhook(
    webhook_url: str,
    message: str | None = None,
    embed: dict | None = None,
    username="School",
):
    cooldown_status = get_cooldown_status()

    if (
        cooldown_status["cooldown_required"]
        and cooldown_status["remaining_expiry"] > datetime.now()
    ):
        seconds_left = (
            cooldown_status["remaining_expiry"] - datetime.now()
        ).total_seconds()

        logger.debug(
            f"Discord webhook rate limit reached, sleeping for {seconds_left}s"
        )

        sleep(seconds_left)

        set_cooldown_status(False, datetime.now())

    data = {"content": message, "username": username}

    if embed is not None:
        data["embeds"] = [embed]

    # Send the message to the Discord webhook
    response = requests.post(webhook_url, json=data)

    if response.status_code != 204:
        raise ValueError(
            f"Discord webhook returned status code {response.status_code}",
            response.text,
        )

    # Check X-RateLimit-Limit and X-RateLimit-Remaining headers
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_after = response.headers.get("X-RateLimit-Reset-After")

    if remaining is None or reset_after is None:
        return

    remaining = int(remaining)

    if remaining == 1:
        expiry = datetime.now() + timedelta(seconds=float(reset_after))
        set_cooldown_status(True, expiry)
