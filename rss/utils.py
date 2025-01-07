import json

import feedparser
import trafilatura


def parse_rss_feed(feed: str):
    feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
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
