import os
from time import sleep

import dotenv
import requests

from lib.redis import redis_client

dotenv.load_dotenv()


def send_discord(message: str, username: str = "School"):
    url = os.getenv("DISCORD_WEBHOOK_URL")

    # Throw an error if the webhook URL is not provided
    if url is None:
        raise ValueError(
            "Discord webhook URL is not provided in the environment variables"
        )

    # Check the rate limit
    remaining = redis_client.get("discord_rate_limit_limit")
    remaining_expiry = redis_client.ttl("discord_rate_limit_limit")

    if remaining is not None and int(remaining) == 0:
        sleep(remaining_expiry)

    # Send the message to the Discord webhook
    response = requests.post(url, json={"content": message, "username": username})

    if response.status_code != 204:
        raise ValueError(f"Discord webhook returned status code {response.status_code}")

    # Check X-RateLimit-Limit and X-RateLimit-Remaining headers
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_after = response.headers.get("X-RateLimit-Reset-After")
    redis_client.set("discord_rate_limit_limit", int(remaining), ex=int(reset_after))
