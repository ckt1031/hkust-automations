import hashlib
import json
import re
from datetime import datetime, timezone

import feedparser
import trafilatura
from dateutil import parser
from loguru import logger
from pydantic import BaseModel

from lib.config import BROWSER_USER_AGENT
from lib.openai_api import generate_schema


def sha2_256(text: str) -> str:
    return hashlib.sha3_256(text.encode()).hexdigest()


def get_ms(date: str):
    parsed_date = parser.parse(date)

    # Ensure parsed_date is timezone-aware
    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)

    return parsed_date.timestamp()


def clean_html(raw_html: str) -> str:
    """
    Clean HTML tags from the raw HTML content
    """

    clean = re.compile("<.*?>")  # Regular expression to match HTML tags
    return re.sub(clean, "", raw_html)  # Return text without HTML tags


# Function to remove CSS and scripts from HTML
def remove_css_and_scripts(raw_html: str) -> str:
    """
    Remove CSS and scripts from the HTML content
    """
    # Remove style tags
    raw_html = re.sub(r"<style.*?>.*?</style>", "", raw_html, flags=re.DOTALL)
    # Remove script tags
    raw_html = re.sub(r"<script.*?>.*?</script>", "", raw_html, flags=re.DOTALL)
    return raw_html


def extract_content_from_url(original_content: str) -> str:
    class Schema(BaseModel):
        article_urls: list[str]

    prompt = """Extract article URL from the text, it must be valid articles or some website which has information.
    Non-article URL is not allowed, e.g. image, video, youtube, twitter, etc.
    """

    res = generate_schema(
        system_message=prompt,
        user_message=original_content,
        schema=Schema,
    )

    article_urls = res.article_urls

    if not article_urls:
        return ""

    content = ""

    for url in article_urls:
        try:
            logger.info(f"Extracted article URL: {url}")

            article = extract_website(url)
            text = article["raw_text"]

            content += f"Title: {article['title']}\nContent: {text}\n"
        except Exception as e:
            logger.error(f"Failed to extract article URL: {url}, error: {e}")

    return content


MAXIMUM_CHECK_DAYS = 5


def exceed_maximum_check_days(date: str) -> bool:
    ms = get_ms(date)

    now = datetime.now(timezone.utc).timestamp()

    return (now - ms) > MAXIMUM_CHECK_DAYS * 24 * 60 * 60


def parse_rss_feed(feed: str):
    feedparser.USER_AGENT = BROWSER_USER_AGENT
    return feedparser.parse(feed, request_headers={"Connection": "keep-alive"})


def extract_website(link: str):
    downloaded = trafilatura.fetch_url(link)
    json_data = trafilatura.extract(
        downloaded,
        output_format="json",
        with_metadata=True,
    )

    if json_data is None:
        raise ValueError("No content extracted from the website")

    # Each item
    # title, link, summary, published, id, author
    return json.loads(json_data)
