import sys
from datetime import datetime, timedelta, timezone

from loguru import logger

from canvas.api import get_conversation_detail, get_conversations
from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store


def check_canvas_inbox():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")

    if webhook_url is None:
        logger.error(
            "DISCORD_WEBHOOK_URL_CANVAS is not provided in the environment variables"
        )
        sys.exit(1)

    conversations = get_conversations()

    if len(conversations) == 0:
        logger.success("No conversations to check")
        return

    store_path = "canvas_inbox_reminder.json"
    store = get_store(store_path)

    for conversation in conversations:
        last_message_at = datetime.fromisoformat(conversation["last_message_at"])

        # Check if the conversation has been longer than 72 hours
        if last_message_at < (datetime.now(timezone.utc) - timedelta(hours=72)):
            logger.info(
                f"Conversation {conversation['id']} has been longer than 72 hours, skipping"
            )
            continue

        # Check if the conversation has already been recorded
        if str(conversation["id"]) in store:
            logger.info(f"Conversation {conversation['id']} was recorded, skipping")
            continue

        detail = get_conversation_detail(conversation["id"])
        content = detail["messages"][0]["body"]

        if len(content) > 1700:
            content = content[:1700] + "..."

        embed = {
            "title": f"New Conversation: {conversation['subject']}",
            "description": content,
            "footer": {"text": conversation["context_name"]},
            "author": {
                "name": conversation["participants"][0]["name"],
                "icon_url": conversation["avatar_url"],
            },
        }

        send_discord_webhook(webhook_url, embed=embed)

        logger.success(f"Conversation {conversation['id']} sent to Discord")

        # Add the conversation to the records
        store[str(conversation["id"])] = datetime.now(timezone.utc)

    save_store(store_path, store)

    logger.success("Inbox checked successfully")
