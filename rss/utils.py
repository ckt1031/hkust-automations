import json

import feedparser
import trafilatura

from lib.config import BROWSER_USER_AGENT


def parse_rss_feed(feed: str):
    feedparser.USER_AGENT = BROWSER_USER_AGENT
    return feedparser.parse(feed, request_headers={"Connection": "keep-alive"})


def extract_website(link: str):
    downloaded = trafilatura.fetch_url(link)
    json_data = trafilatura.extract(
        downloaded, output_format="json", with_metadata=True
    )

    if json_data is None:
        raise ValueError("No content extracted from the website")

    # Each item
    # title, link, summary, published, id, author
    return json.loads(json_data)
