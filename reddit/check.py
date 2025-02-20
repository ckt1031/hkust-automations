from datetime import datetime, timezone

import html2text
from loguru import logger

from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from lib.utils import extract_content_from_url
from prompts.reddit import RedditMassPostsResponse, reddit_prompts
from rss.news import exceed_maximum_check_days
from rss.utils import parse_rss_feed


def extract_reddit_content_with_comments(link: str) -> str | None:
    feed_link = link + ".rss"

    feed_data = parse_rss_feed(feed_link)

    if not feed_data or len(feed_data.entries) == 0:
        logger.info(f"No reddit comments found for {link}")
        return None

    # Since the RSS will return the post and comments, we need to extract the comments
    # But we want to get posts with comments, but ignore posts without comments

    # If it has only one entry, it is a post without comments
    if len(feed_data.entries) == 1:
        logger.info(f"No comments found for {link}")
        return None

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
        raise ValueError("DISCORD_WEBHOOK_URL_REDDIT not set")

    reddit_link = "https://www.reddit.com/r/HKUST"
    feed_link = f"{reddit_link}.rss"

    feed_data = parse_rss_feed(feed_link)

    if not feed_data or len(feed_data.entries) == 0:
        logger.info("No new entries found")
        return

    logger.info(
        f"Found {len(feed_data.entries)} entries in Reddit - {feed_data.feed.title}"
    )

    store_path = "reddit.json"
    store = get_store_with_datetime(store_path)

    reddit_posts: list[dict] = []

    # Stage 1: Store information of posts and comments to memory
    for entry in feed_data.entries:
        # Check the date first
        if exceed_maximum_check_days(entry.published):
            logger.info(f"Reddit too old: {entry.link}, skip")
            continue

        reddit_post_id = entry.link.replace(f"{reddit_link}/comments/", "").split("/")[
            0
        ]

        if f"{reddit_link}/comments/{reddit_post_id}" in store:
            logger.info(f"Reddit already scraped: {entry.link}, skip")
            continue

        logger.info(f"Checking Reddit: {entry.link}")

        reddit_full_content = extract_reddit_content_with_comments(entry.link)

        if not reddit_full_content or len(reddit_full_content) == 0:
            logger.info(f"No content found for {entry.link}, skip")
            continue

        reddit_posts.append(
            {
                "id": reddit_post_id,
                "link": entry.link,
                "content": reddit_full_content,
            }
        )

    for i in range(0, len(reddit_posts), 5):
        user_prompt = f"Reddit Analysis - {i + 1} to {i + 5}\n\n"

        # Generate the user prompt
        for data in reddit_posts[i : i + 5]:
            user_prompt += f"""ID: {data['id']}
            Link: {data['link']}
            Content: {data['content']}\n\n"""

        res = generate_schema(reddit_prompts, user_prompt, RedditMassPostsResponse)

        if not res:
            logger.info(f"Failed to analyze Reddit - {i + 1} to {i + 5}")
            continue

        ids_to_save = res.accepted_ids + res.rejected_ids

        for _id in ids_to_save:
            link = f"{reddit_link}/comments/{_id}"
            store[link] = datetime.now(tz=timezone.utc)

        logger.success(f"We have stored {len(ids_to_save)} Reddit posts")

        if res.has_summary and len(res.summary) > 0:
            discord_embed = {
                "title": res.whole_title,
                "description": res.summary,
                "color": 0xFF0000,  # Red
            }

            send_discord_webhook(webhook, embed=discord_embed, username="HKUST Reddit")

        save_store_with_datetime(store_path, store)

        logger.success(f"Analyzed Reddit - {i + 1} to {i + 5}")
