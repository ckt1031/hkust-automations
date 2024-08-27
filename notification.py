import os

import dotenv
from discord_webhook import DiscordWebhook

dotenv.load_dotenv()


def send_discord(message: str):
    url = os.getenv("DISCORD_WEBHOOK_URL")

    webhook = DiscordWebhook(url, content=message)
    webhook.execute()
