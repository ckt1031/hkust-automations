import os

from dotenv import load_dotenv

load_dotenv()

CANVAS_API_KEY = os.getenv("CANVAS_API_KEY")

ONEDRIVE_STORE_FOLDER = os.getenv("ONEDRIVE_STORE_FOLDER", "Programs/Information-Push")

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REFRESH_TOKEN = os.getenv("MICROSOFT_REFRESH_TOKEN")

DISCORD_WEBHOOK_URL_NEWS = os.getenv("DISCORD_WEBHOOK_URL_NEWS")
DISCORD_WEBHOOK_URL_INBOX = os.getenv("DISCORD_WEBHOOK_URL_INBOX")
DISCORD_WEBHOOK_URL_EMAILS = os.getenv("DISCORD_WEBHOOK_URL_EMAILS")
DISCORD_WEBHOOK_URL_ASSIGNMENTS = os.getenv("DISCORD_WEBHOOK_URL_ASSIGNMENTS")
