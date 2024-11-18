from datetime import datetime, timezone

from loguru import logger

import lib.env as env
from canvas.api import get_conversation_detail, get_conversations
from lib.notification import send_discord
from lib.onedrive_store import CANVAS_INBOX_REMINDER_PATH, get_record, save_record


def is_conversation_checked(list: list[dict[str, str]], id: str):
    # If id exists in the list as a key, return True
    for item in list:
        if item.get(id):
            return True

    return False


def check_inbox():
    webhook_url = env.DISCORD_WEBHOOK_URL_INBOX

    if webhook_url is None:
        raise ValueError(
            "Discord webhook URL is not provided in the environment variables"
        )

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
        if is_conversation_checked(records, str(conversation["id"])):
            logger.info(
                f"Conversation {conversation['id']} has already been recorded, skipping"
            )
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
