from datetime import datetime, timezone

import html2text
from loguru import logger
from pydantic import BaseModel

from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from prompts.reddit import RedditMassPostsResponse, reddit_prompts
from rss.news import exceed_maximum_check_days
from rss.utils import extract_website, parse_rss_feed


def extract_content_from_url(text: str) -> str:
    class Schema(BaseModel):
        article_urls: list[str]

    prompt = """Extract article URL from the text, it must be valid articles or some website which has information.
    Non-article URL is not allowed, e.g. image, video, youtube, twitter, etc.
    """

    res = generate_schema(
        system_message=prompt,
        user_message=text,
        schema=Schema,
    )

    article_urls = res.article_urls

    if not article_urls:
        return ""

    c = ""

    for url in article_urls:
        logger.info(f"Extracted article URL: {url}")

        article = extract_website(url)
        text = article["raw_text"]

        c += f"Title: {article['title']}\nContent: {text}\n"

    return c


def extract_content_with_comments(url: str) -> str:
    feed_url = url + ".rss"

    feed_data = parse_rss_feed(feed_url)

    if not feed_data or len(feed_data.entries) == 0:
        logger.info("No new entries found")
        return ""

    content = ""

    is_first = True

    for entry in feed_data.entries:
        summary = html2text.html2text(entry.summary)

        if is_first:
            content += f"Post: {entry.title}\nComment: "
            is_first = False
            continue

        content += f"{summary}\n"

    article_content = extract_content_from_url(content)

    return f"{article_content}\n{content}"


def check_reddit():
    webhook = getenv("DISCORD_WEBHOOK_URL_REDDIT")

    if not webhook:
        logger.error("DISCORD_WEBHOOK_URL_REDDIT not set")
        return

    feed_url = "https://www.reddit.com/r/HKUST/.rss"

    feed_data = parse_rss_feed(feed_url)

    if not feed_data or len(feed_data) == 0:
        logger.info("No new entries found")
        return

    logger.info(
        f"Found {len(feed_data)} entries in Reddit - {feed_data['feed']['title']}"
    )

    store_path = "reddit.json"
    store = get_store_with_datetime(store_path)

    reddit_posts: list[dict] = []

    for entry in feed_data.entries:
        # Check the date first
        if exceed_maximum_check_days(entry.published):
            logger.info(f"Reddit too old: {entry.link}, skip")
            continue

        _id = entry.link.replace("https://www.reddit.com/r/HKUST/comments/", "").split(
            "/"
        )[0]

        if f"https://www.reddit.com/r/HKUST/comments/{_id}" in store:
            logger.info(f"Reddit already scraped: {entry.link}, skip")
            continue

        logger.info(f"Checking Reddit: {entry.link}")

        e = extract_content_with_comments(entry.link)

        if not e:
            continue

        logger.success

        reddit_posts.append(
            {
                "url": entry.link,
                "content": e,
            }
        )

    for i in range(0, len(reddit_posts), 5):
        user_prompt = f"Reddit Analysis - {i + 1} to {i + 5}\n\n"
        for data in reddit_posts[i : i + 5]:
            _id = (
                data["url"]
                .replace("https://www.reddit.com/r/HKUST/comments/", "")
                .split("/")[0]
            )

            user_prompt += (
                f"URL: {data['url']}\nID: {_id}\nContent: {data['content']}\n\n"
            )

        res = generate_schema(reddit_prompts, user_prompt, RedditMassPostsResponse)

        if not res:
            logger.info(f"Failed to analyze Reddit - {i + 1} to {i + 5}")
            continue

        ids_to_save = res.accepted_ids + res.rejected_ids

        for _id in ids_to_save:
            link = f"https://www.reddit.com/r/HKUST/comments/{_id}"
            store[link] = datetime.now(tz=timezone.utc)

        logger.success(f"We have stored {len(ids_to_save)} Reddit posts")

        if res.has_summary:
            discord_embed = {
                "title": "Reddit Summary",
                "description": res.summary,
                # Red
                "color": 0xFF0000,
            }

            send_discord_webhook(webhook, embed=discord_embed, username="HKUST Reddit")

        save_store_with_datetime(store_path, store)

        logger.success(f"Analyzed Reddit - {i + 1} to {i + 5}")
