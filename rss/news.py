import sys
from datetime import datetime, timezone
from enum import Enum

from loguru import logger

import lib.env as env
from discord.webhook import send_discord
from lib.llm import llm_generate
from lib.onedrive_store import RSS_NEWS_RECORD_PATH, get_store, save_store
from lib.utils import get_ms, sha2_256
from prompts.summary import summary_prompt
from rss.utils import extract_website, parse_rss_feed

RSS_LIST = [
    "https://itsc.hkust.edu.hk/rss.xml",
]

MAXMIUM_CHECK_DAYS = 5


def exceed_maximum_check_days(date: str) -> bool:
    ms = get_ms(date)

    now = datetime.now(timezone.utc).timestamp()

    return (now - ms) > MAXMIUM_CHECK_DAYS * 24 * 60 * 60


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

        llm_response = llm_generate(summary_prompt, user_prompt)

        embed = {
            "title": rss_item["title"],
            "description": llm_response,
            "url": link,
            "color": 0x013466,
        }

        send_discord(webhook, None, embed, "HKUST News")

        return RSSItemStatus.OK
    except Exception as e:
        logger.error(f"Failed to extract website and summarize content: {link}")
        logger.error(e)
        return RSSItemStatus.FAIL


def check_rss_news():
    if env.DISCORD_WEBHOOK_URL_NEWS is None:
        logger.error("DISCORD_WEBHOOK_URL_NEWS is not set")
        sys.exit(1)

    logger.info("Checking RSS news...")

    store = get_store(RSS_NEWS_RECORD_PATH)

    for rss in RSS_LIST:
        logger.info(f"Checking RSS: {rss}")
        data = parse_rss_feed(rss)

        for item in data:
            key = sha2_256(item["id"])

            if key in store:
                logger.info(f"RSS item already checked: {item['title']}")
                continue

            status = check_single_rss_item(env.DISCORD_WEBHOOK_URL_NEWS, item)

            if status == RSSItemStatus.FAIL:
                continue

            store[key] = datetime.now(timezone.utc)

            logger.success(f"RSS item checked: {item['link']}")

    save_store(RSS_NEWS_RECORD_PATH, store)

    logger.success("RSS news checked")
