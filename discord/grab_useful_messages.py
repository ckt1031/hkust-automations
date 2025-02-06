import re
import time
from datetime import datetime, timezone

from loguru import logger

from discord.api import get_channel_info, get_channel_messages, get_guild_info
from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from prompts.discord_useful_summary import DiscordSummarySchema, discord_summary_prompts

server_channel_list = {
    # HKUST FYS Discord Server
    "880301598981648416": [
        "880301599665295414",  # 吹水場
        "880301599665295415",  # 新生討論區
        "881790721298952203",  # 讀書研習坊
        "881792090722426880",  # 搵工上班族
        "1174738355922157688",  # 校務關注組
        "880326266719465482",  # 校園動態牆
    ]
}


def purify_message_content(message: str):
    """
    Replace all emojis with a space
    """

    message = re.sub(r"<a?:\w+:\d+>", " ", message)

    return message


def filter_messages(messages: list) -> list:
    """
    Filter off bot messages and purify the message content
    """
    filtered_messages = []

    for message in messages:
        if message["type"] == 0:
            if "bot" in message["author"] and message["author"]["bot"]:
                continue

            message["content"] = purify_message_content(message["content"])

            filtered_messages.append(message)

    return filtered_messages


def handle_channel(channel: dict, messages: list) -> bool:
    webhook_url = getenv("DISCORD_WEBHOOK_URL_DISCORD_SUMMARY")

    user_prompts = ""

    for message in messages:
        author = message["author"]
        username = f"User: {author['global_name']}"

        has_equal_global_name = (
            (author["global_name"].lower() != author["username"].lower())
            if "global_name" in author and author["global_name"] is not None
            else False
        )

        if has_equal_global_name:
            username += f" ({author['username']})"

        _draft = f"{username}\nContent: {message['content']}"

        if len(message["embeds"]) > 0:
            for embed in message["embeds"]:
                if embed["type"] == "video":
                    _draft += (
                        f"\nVideo: {embed['title']} - ({embed.get('description', '')})"
                    )
                elif embed["type"] == "link" or embed["type"] == "rich":
                    _draft = "\nLink: "

                    if "title" in embed:
                        _draft += f"{embed['title']} "

                    if "description" in embed:
                        _draft += f"({embed['description']})"

        user_prompts += _draft + "\n\n"

    response = generate_schema(
        discord_summary_prompts, user_prompts, DiscordSummarySchema
    )

    if not response.available or len(response.summary) == 0:
        logger.info(
            f"No valuable message for {channel['name']} ({channel['guild']["name"]})"
        )
        return False

    embed = {
        "title": f"Summary of {channel['name']}",
        "description": response.summary.rstrip(),
        "url": f"https://discord.com/channels/{channel['guild_id']}/{channel['id']}",
        "footer": {
            "text": channel["guild"]["name"],
        },
        "color": 0x4950FE,
    }

    send_discord_webhook(webhook_url, embed=embed)

    return True


def get_useful_messages():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_DISCORD_SUMMARY")

    if webhook_url is None:
        raise ValueError(
            "DISCORD_WEBHOOK_URL_DISCORD_SUMMARY is not provided in the environment variables"
        )

    store_path = "discord_channel_summary.json"
    store = get_store_with_datetime(store_path)

    for server_id, channel_ids in server_channel_list.items():
        guild = get_guild_info(server_id)
        for channel_id in channel_ids:
            channel_info = get_channel_info(server_id, channel_id)

            channel_info["guild"] = guild

            logger.info(
                f"GET messages from \"{channel_info['name']}\" in \"{guild['name']}\""
            )

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
                logger.info(
                    f"No valuable message for {channel_info['name']} ({guild['name']})"
                )
                continue

            status = handle_channel(channel_info, final_checking_messages)

            if status:
                store[channel_info["id"]] = current_time

                save_store_with_datetime(store_path, store)

                logger.success(f"Successfully summarized {channel_info['name']}")

            logger.debug("Sleeping for 5 seconds to cooldown...")

            time.sleep(5)

    logger.success("All Discord channels have been checked and summarized")
