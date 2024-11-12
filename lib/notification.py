from time import sleep

import requests

REMAINING = -1
REMAINING_EXPIRY = -1


def send_discord(
    webhook_url: str, message: str | None, embed: dict | None, username: str = "School"
):
    global REMAINING, REMAINING_EXPIRY

    if REMAINING_EXPIRY is not None and int(REMAINING_EXPIRY) == 0:
        sleep(REMAINING_EXPIRY)

    # Send the message to the Discord webhook
    response = requests.post(
        webhook_url, json={"content": message, "username": username, "embeds": [embed]}
    )

    if response.status_code != 204:
        raise ValueError(f"Discord webhook returned status code {response.status_code}")

    # Check X-RateLimit-Limit and X-RateLimit-Remaining headers
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_after = response.headers.get("X-RateLimit-Reset-After")

    if remaining is None or reset_after is None:
        return

    REMAINING = int(remaining)
    REMAINING_EXPIRY = int(reset_after)
