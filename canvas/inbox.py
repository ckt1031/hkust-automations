import sys
from datetime import datetime, timezone

from loguru import logger

import lib.env as env
from canvas.api import get_conversation_detail, get_conversations
from lib.notification import send_discord
from lib.onedrive_store import (
    CANVAS_INBOX_REMINDER_PATH,
    get_record,
    is_recorded,
    save_record,
)


def check_inbox():
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

    records = get_record(CANVAS_INBOX_REMINDER_PATH)
    iso_time = datetime.now(timezone.utc).astimezone().isoformat()

    for conversation in conversations:
        # Check if the conversation has been longer than 72 hours
        if (
            datetime.now(timezone.utc)
            - datetime.fromisoformat(conversation["last_message_at"])
        ).days > 3:
            logger.info(
                f"Conversation {conversation['id']} has been longer than 72 hours, skipping"
            )
            continue

        # Check if the conversation has already been recorded
        if is_recorded(records, str(conversation["id"])):
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

        logger.success(f"Conversation {conversation['id']} sent to Discord")

        # Add the conversation to the records
        records.append({str(conversation["id"]): iso_time})

    save_record(CANVAS_INBOX_REMINDER_PATH, records)

    logger.success("Inbox checked successfully")
