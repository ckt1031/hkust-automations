import os

import dotenv
from discord_webhook import DiscordWebhook

dotenv.load_dotenv()


def send_discord(message: str, username: str = "School"):
    url = os.getenv("DISCORD_WEBHOOK_URL")

    # Throw an error if the webhook URL is not provided
    if url is None:
        raise ValueError(
            "Discord webhook URL is not provided in the environment variables"
        )

    webhook = DiscordWebhook(url, content=message, username=username)
    webhook.execute()
