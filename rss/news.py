import sys
from datetime import datetime, timezone
from enum import Enum

from loguru import logger

from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store
from lib.openai_api import generate_chat_completion
from lib.utils import get_ms, sha2_256
from prompts.summary import summary_prompt
from rss.utils import extract_website, parse_rss_feed

RSS_LIST = [
    "https://itsc.hkust.edu.hk/rss.xml",
]

MAXIMUM_CHECK_DAYS = 5


def exceed_maximum_check_days(date: str) -> bool:
    ms = get_ms(date)

    now = datetime.now(timezone.utc).timestamp()

    return (now - ms) > MAXIMUM_CHECK_DAYS * 24 * 60 * 60


class RSSItemStatus(Enum):
    OK = 0
    SKIP = 1
    FAIL = 2


def check_single_rss_item(webhook: str, rss_item) -> RSSItemStatus:
    link = rss_item["link"]

    try:
        article = extract_website(link)
        logger.info(f"Article: {article['title']} posted on {article['date']}")

        if exceed_maximum_check_days(article["date"]):
            logger.info(f"Article is too old: {article['date']}, skip")
            return RSSItemStatus.SKIP

        user_prompt = f"""
            Date: {article["date"]}
            Title: {article["title"]}
            Link: {link}
            Content: {article['raw_text']}
        """

        llm_response = generate_chat_completion(summary_prompt, user_prompt)

        embed = {
            "title": rss_item["title"],
            "description": llm_response,
            "url": link,
            "color": 0x013466,
        }

        send_discord_webhook(webhook, embed=embed, username="HKUST News")

        return RSSItemStatus.OK
    except Exception as e:
        logger.error(f"Failed to extract website and summarize content: {link}")
        logger.error(e)
        return RSSItemStatus.FAIL


def check_rss_news():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_NEWS")

    if webhook_url is None:
        logger.error("DISCORD_WEBHOOK_URL_NEWS is not set")
        sys.exit(1)

    logger.info("Checking RSS news...")

    store_path = "rss_news_record.json"
    store = get_store(store_path)

    for rss in RSS_LIST:
        logger.info(f"Checking RSS: {rss}")
        data = parse_rss_feed(rss)

        for item in data:
            key = sha2_256(item["id"])

            if key in store:
                logger.info(f"RSS item already checked: {item['title']}")
                continue

            status = check_single_rss_item(webhook_url, item)

            if status == RSSItemStatus.FAIL:
                continue

            store[key] = datetime.now(timezone.utc)

            logger.success(f"RSS item checked: {item['link']}")

    save_store(store_path, store)

    logger.success("RSS news checked")
