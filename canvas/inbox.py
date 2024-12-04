import sys
from datetime import datetime, timedelta, timezone

from loguru import logger

import lib.env as env
from canvas.api import get_conversation_detail, get_conversations
from lib.notification import send_discord
from lib.onedrive_store import CANVAS_INBOX_REMINDER_PATH, get_store, save_store


def check_canvas_inbox():
    webhook_url = env.DISCORD_WEBHOOK_URL_INBOX

    if webhook_url is None:
        logger.error(
            "Discord webhook URL is not provided in the environment variables (DISCORD_WEBHOOK_URL_INBOX)"
        )
        sys.exit(1)

    conversations = get_conversations()

    if len(conversations) == 0:
        logger.success("No conversations to check")
        return

    store = get_store(CANVAS_INBOX_REMINDER_PATH)

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

        send_discord(webhook_url, None, embed)

        logger.success(f"Conversation {conversation.id} sent to Discord")

        # Add the conversation to the records
        store[str(conversation["id"])] = datetime.now(timezone.utc)

    save_store(CANVAS_INBOX_REMINDER_PATH, store)

    logger.success("Inbox checked successfully")
