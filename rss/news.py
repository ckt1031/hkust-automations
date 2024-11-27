import sys
from datetime import datetime, timezone
from enum import Enum

from loguru import logger

import lib.env as env
from lib.llm import LLM
from lib.notification import send_discord
from lib.onedrive_store import (
    RSS_NEWS_RECORD_PATH,
    get_record_list,
    is_recorded,
    save_record,
)
from lib.utils import get_current_iso_time, get_ms, sha2_256
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

        llm = LLM()
        llm_response = llm.run_chat_completion(summary_prompt, user_prompt)

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

    record = get_record_list(RSS_NEWS_RECORD_PATH)
    current_iso = get_current_iso_time()

    for rss in RSS_LIST:
        logger.info(f"Checking RSS: {rss}")
        data = parse_rss_feed(rss)

        for item in data:
            key = sha2_256(item["id"])

            if is_recorded(record, key):
                logger.info(f"RSS item already checked: {item['title']}")
                continue

            status = check_single_rss_item(env.DISCORD_WEBHOOK_URL_NEWS, item)

            if status == RSSItemStatus.FAIL:
                continue

            record.append({key: current_iso})

            logger.success(f"RSS item checked: {item['link']}")

    save_record(RSS_NEWS_RECORD_PATH, record)

    logger.success("RSS news checked")
