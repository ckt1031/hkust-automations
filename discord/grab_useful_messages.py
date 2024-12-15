import re
import time
from datetime import datetime, timezone

from loguru import logger

from discord.api import get_channel_info, get_channel_messages
from discord.webhook import send_discord_webhook
from lib.env import Environment
from lib.onedrive_store import get_store, save_store
from lib.openai import generate_chat_completion
from prompts.discord_useful_summary import discord_summary_prompts

server_channel_list = {
    # HKUST FYS Discord Server
    "880301598981648416": [
        "880301599665295414",  # atrium-gossip 吹水場
        "880301599665295415",  # freshmen-新生討論區
        "881790721298952203",  # studying讀書研習坊
        # "881792090722426880",  # work-experience搵工上班族
        "881792090722426880",  # campus-affairs校務關注組
        "880326266719465482",  # campus-news校園動態牆
    ]
}


def purify_message_content(message: str):
    # Replace all emojis with a space
    message = re.sub(r"<a?:\w+:\d+>", " ", message)

    return message


def filter_messages(messages: list) -> list:
    filtered_messages = []

    for message in messages:
        if message["type"] == 0:
            if "bot" in message["author"] and message["author"]["bot"]:
                continue

            message["content"] = purify_message_content(message["content"])

            filtered_messages.append(message)

    return filtered_messages


def handle_channel(channel: dict, messages: list) -> bool:
    webhook_url = Environment.get("DISCORD_WEBHOOK_URL_DISCORD_SUMMARY")

    if webhook_url is None:
        logger.error(
            "DISCORD_WEBHOOK_URL_DISCORD_SUMMARY is not provided in the environment variables"
        )
        return False

    user_prompts = ""

    for message in messages:
        _draft = f"User: {message['author']['username']}\nContent: {message['content']}"

        if len(message["embeds"]) > 0:
            for embed in message["embeds"]:
                if embed["type"] == "video":
                    _draft += f"\nVideo: {embed['title']} - ({embed['description']})"
                elif embed["type"] == "link" or embed["type"] == "rich":
                    _draft = "\nLink: "

                    if "title" in embed:
                        _draft += f"{embed['title']} "

                    if "description" in embed:
                        _draft += f"({embed['description']})"

        user_prompts += _draft + "\n\n"

    response = generate_chat_completion(discord_summary_prompts, user_prompts)

    if response.strip().lower() == "no":
        logger.info("No valuable message to summarize and construct points.")
        return False

    embed = {
        "title": f"Summary of {channel['name']}",
        "description": f"{response.rstrip()}\n\n<#{channel['id']}>",
        "timestamp": datetime.now(tz=timezone.utc).astimezone().isoformat(),
    }

    send_discord_webhook(webhook_url, embed=embed)

    return True


def get_useful_messages():
    store_path = "discord_channel_summary.json"
    store = get_store(store_path)

    for server_id, channel_ids in server_channel_list.items():
        for channel_id in channel_ids:
            channel_info = get_channel_info(server_id, channel_id)

            logger.info(f"Getting messages from {channel_info['name']}")

            messages = get_channel_messages(
                server_id,
                channel_id,
            )

            filtered_messages = filter_messages(messages)

            # Timestamp checking
            current_time = datetime.now(tz=timezone.utc)

            previous_checked_date: datetime = (
                store[channel_info["id"]] if channel_info["id"] in store else None
            )

            final_checking_messages = []

            for message in filtered_messages:
                if not previous_checked_date:
                    final_checking_messages.append(message)
                    continue

                message_timestamp = datetime.fromisoformat(message["timestamp"])

                if message_timestamp > previous_checked_date:
                    final_checking_messages.append(message)

            if len(final_checking_messages) == 0:
                logger.info("No valuable message to summarize and construct points.")
                continue

            status = handle_channel(channel_info, final_checking_messages)

            if status:
                store[channel_info["id"]] = current_time

                save_store(store_path, store)

                logger.success(
                    f"Successfully summarized and constructed points for {channel_info['name']}"
                )

            logger.info(
                "Sleeping for 5 seconds before getting messages from the next channel, wait for it..."
            )

            time.sleep(5)
