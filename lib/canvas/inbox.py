from datetime import datetime, timedelta, timezone

from loguru import logger

from lib.api.canvas import get_conversation_detail, get_conversations
from lib.api.discord import send_discord_webhook
from lib.api.onedrive import get_store_with_datetime, save_store_with_datetime
from lib.api.openai import generate_chat_completion
from lib.env import getenv
from lib.prompts.summary import summary_prompt


def notify_canvas_new_canvas_inbox():
    webhook_url = getenv("DISCORD_WEBHOOK_CANVAS", required=True)

    conversations = get_conversations()

    if len(conversations) == 0:
        logger.success("No conversations to check")
        return

    store_path = "canvas_inbox_reminder.json"
    store = get_store_with_datetime(store_path)

    for conversation in conversations:
        last_message_at = datetime.fromisoformat(conversation["last_message_at"])

        # Check if the conversation has been longer than 72 hours
        if last_message_at < (datetime.now(timezone.utc) - timedelta(hours=72)):
            logger.debug(
                f"Conversation {conversation['id']} has been longer than 72 hours, skipping"
            )
            continue

        # Check if the conversation has already been recorded
        if str(conversation["id"]) in store:
            logger.info(f"Conversation {conversation['id']} was recorded, skipping")
            continue

        detail = get_conversation_detail(conversation["id"])

        if "context_name" not in conversation or conversation["context_name"] is None:
            conversation["context_name"] = "Canvas"

        content = f"Context: {conversation["context_name"]}\nTitle: {conversation['subject']}\nContent: {detail["messages"][0]["body"]}"
        llm_response = generate_chat_completion(summary_prompt, content)

        embed = {
            "title": f"Conversation: {conversation['subject']}",
            "description": llm_response,
            "footer": {
                "text": conversation["context_name"].strip() + " Inbox",
            },
            "author": {
                "name": conversation["participants"][0]["name"],
                "icon_url": conversation["avatar_url"],
            },
            "color": 0xFF5DB6,
        }

        send_discord_webhook(webhook_url, embed=embed)

        logger.success(f"Conversation {conversation['id']} sent to Discord")

        # Add the conversation to the records
        store[str(conversation["id"])] = datetime.now(timezone.utc)

        save_store_with_datetime(store_path, store)

        logger.success("Canvas Inbox checked successfully")
