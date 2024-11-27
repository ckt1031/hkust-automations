import re
import time

from loguru import logger

from datetime import datetime
from discord.api import get_channel_info, get_channel_messages
from lib import env
from lib.llm import LLM
from lib.notification import send_discord
from lib.onedrive_store import (
    DISCORD_CHANNEL_SUMMARY_PATH,
    get_record,
    save_record,
)
from lib.utils import get_current_iso_time

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


def filter_messages(messages) -> list[dict]:
    filtered_messages = []

    for message in messages:
        if message["type"] == 0:
            if "bot" in message["author"] and message["author"]["bot"]:
                continue

            message["content"] = purify_message_content(message["content"])

            filtered_messages.append(message)

    return filtered_messages


def handle_channel(channel, messages) -> bool:
    user_prompts = ""
    system_prompts = """
You are now a chat summarize bot, you will be given a list of messages from a channel,
only grab useful information from Discord Server, respond with a summary of the messages in points.
    
1. Exclude user names, only include the most important information.
2. Include links in markdown format, and videos in markdown format if they are important.
3. Ensure points are clear and unstandable.
4. Include date and time of some specific dated information.
5. For important embeds, use markdown links, do not use URL as the link text, use the title of the link.
    Then include all link or video related details, like title, description if available.
6. Ignore all irrelevant information, GIFs, and emojis, like :place_of_worship:, some joke or some unknown terms, abbreviations or slangs.

Return "NO" as the only output if there are no or valuable message to summarize and construct points.
    """

    for message in messages:
        _draft = f"User: {message['author']['username']}\nContent: {message['content']}"

        if len(message["embeds"]) > 0:
            for embed in message["embeds"]:
                if embed["type"] == "video":
                    _draft += f"\nVideo: {embed['title']} - ({embed['description']})"
                elif embed["type"] == "link":
                    _draft += f"\nLink: {embed['title']} - ({embed['description'] if 'description' in embed else ''})"

        user_prompts += _draft + "\n\n"

    llm = LLM()
    response = llm.run_chat_completion(system_prompts, user_prompts)

    if response.strip().lower() == "no":
        logger.info("No valuable message to summarize and construct points.")
        return False

    embed = {
        "title": f"Summary of {channel['name']}",
        "description": f"{response.rstrip()}\n\n<#{channel['id']}>",
        "timestamp": get_current_iso_time(),
    }

    send_discord(
        env.DISCORD_WEBHOOK_URL_DISCORD_NEWS,
        None,
        embed,
    )

    return True


def get_useful_messages():
    record = get_record(DISCORD_CHANNEL_SUMMARY_PATH)

    for server_id, channel_ids in server_channel_list.items():
        for channel_id in channel_ids:
            channel_info = get_channel_info(server_id, channel_id)

            logger.info(f"Getting messages from {channel_info['name']}")

            messages: list[dict] = get_channel_messages(
                server_id,
                channel_id,
            )

            filtered_messages = filter_messages(messages)

            # Timestamp checking
            current_iso = get_current_iso_time()
            previous_checked_iso: str = record[channel_info["id"]] if channel_info["id"] in record else None

            final_checking_messages = []

            for message in filtered_messages:
                if previous_checked_iso:
                    # Compare milliseconds
                    previous_checked_timestamp = datetime.fromisoformat(previous_checked_iso).timestamp()
                    current_timestamp = datetime.fromisoformat(message['timestamp']).timestamp()

                    if current_timestamp > previous_checked_timestamp:
                        final_checking_messages.append(message)
                else:
                    final_checking_messages.append(message)

            if len(final_checking_messages) == 0:
                logger.info("No valuable message to summarize and construct points.")
                continue

            status = handle_channel(channel_info, final_checking_messages)

            if status:
                record[channel_info["id"]] = current_iso

                save_record(DISCORD_CHANNEL_SUMMARY_PATH, record)

                logger.success(
                    f"Successfully summarized and constructed points for {channel_info['name']}"
                )

            logger.info(
                "Sleeping for 5 seconds before getting messages from the next channel, wait for it..."
            )

            time.sleep(5)
