import re
import time

from loguru import logger

from discord.api import get_channel_info, get_channel_messages
from lib import env
from lib.llm import LLM
from lib.notification import send_discord
from lib.onedrive_store import (
    DISCORD_CHANNEL_SUMMARY_PATH,
    get_record,
    is_recorded,
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


def filter_messages(messages):
    filtered_messages = []

    for message in messages:
        if message["type"] == 0:
            if "bot" in message["author"] and message["author"]["bot"]:
                continue

            message["content"] = purify_message_content(message["content"])

            filtered_messages.append(message)

    return filtered_messages


def handle_channel(channel, messages) -> bool:
    channel_id = channel["id"]
    user_prompts = ""
    system_prompts = """
    You are now a chat summarize bot, you will be given a list of messages from a channel,
    only grab useful information from Discord Server, respond with a summary of the messages in points.
    
    Do not include user names, and only include the most important information.
    You might include links in markdown format, and videos in markdown format if they are important.
    Ensure points are clear and unstandable.

    Ignore all irrelevant information, GIFs, and emojis, like :place_of_worship:, some joke or some unknown terms, abbreviations or slangs.
    
    For markdown links, do not use URL as the link text, use the title of the link.

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
        "title": f"<#{channel_id}>",
        "description": response,
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
    current_iso = get_current_iso_time()

    for server_id, channel_ids in server_channel_list.items():
        for channel_id in channel_ids:
            channel_info = get_channel_info(server_id, channel_id)

            logger.info(f"Getting messages from {channel_info['name']}")

            messages: list[dict] = get_channel_messages(
                server_id,
                channel_id,
            )

            for message in messages:
                if is_recorded(record, message["id"]):
                    messages.remove(message)

            filtered_messages = filter_messages(messages)

            if len(filtered_messages) == 0:
                logger.info("No valuable message to summarize and construct points.")
                continue

            status = handle_channel(channel_info, filtered_messages)

            if status:
                for msg in filtered_messages:
                    record.append({msg["id"]: current_iso})

                save_record(DISCORD_CHANNEL_SUMMARY_PATH, record)

            logger.info(
                "Sleeping for 5 seconds before getting messages from the next channel, wait for it..."
            )

            time.sleep(5)
