import os
from time import sleep

import dotenv
import requests

REMAINING = -1
REMAINING_EXPIRY = -1

dotenv.load_dotenv()


def send_discord(message: str, username: str = "School"):

    global REMAINING, REMAINING_EXPIRY

    url = os.getenv("DISCORD_WEBHOOK_URL")

    # Throw an error if the webhook URL is not provided
    if url is None:
        raise ValueError(
            "Discord webhook URL is not provided in the environment variables"
        )

    if REMAINING_EXPIRY is not None and int(REMAINING_EXPIRY) == 0:
        sleep(REMAINING_EXPIRY)

    # Send the message to the Discord webhook
    response = requests.post(url, json={"content": message, "username": username})

    if response.status_code != 204:
        raise ValueError(f"Discord webhook returned status code {response.status_code}")

    # Check X-RateLimit-Limit and X-RateLimit-Remaining headers
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_after = response.headers.get("X-RateLimit-Reset-After")

    if remaining is None or reset_after is None:
        return

    REMAINING = int(remaining)
    REMAINING_EXPIRY = int(reset_after)
