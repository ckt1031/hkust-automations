import json

import feedparser
import trafilatura

# def save_json(content):
#     with open("data.json", "w") as f:
#         json.dump(content, f)


def parse_rss_feed(feed: str):
    rss_feed = feedparser.parse(feed)
    return rss_feed.entries


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
