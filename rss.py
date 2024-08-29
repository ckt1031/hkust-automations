import asyncio
import os

import dotenv
import feedparser
import requests
from playwright.async_api import async_playwright

from db import get_ms, hash_string_sha256, is_record_exist, save_record
from llm import LLM
from notification import send_discord

dotenv.load_dotenv()

RSS_LIST = [
    "https://itsc.hkust.edu.hk/rss.xml",
    # "https://calendar.hkust.edu.hk/rss.xml",
]


def read_news_system_prompt():
    with open("prompts/news.txt", "r") as f:
        return f.read()


async def scrape_body(url):
    async with async_playwright() as p:
        # Launch a browser (you can use 'chromium', 'firefox', or 'webkit')
        browser = await p.webkit.launch()
        page = await browser.new_page()

        # Navigate to the specified URL
        await page.goto(url)

        # Wait for the element with class 'body' to be visible
        await page.wait_for_selector(".body")

        # Get the text content of the element
        body_content = await page.query_selector(".body")
        text_content = ""

        if body_content:
            text_content = await body_content.inner_text()

        # Close the browser
        await browser.close()

        return text_content


def get_feed(url):
    feed = feedparser.parse(url)
    return feed


class RSS:
    def __init__(self):
        feeds = []

        for rss in RSS_LIST:
            feed = get_feed(rss)

            if feed.status == 200:
                for entry in feed.entries:
                    key = hash_string_sha256(f"RSS {entry.link}")

                    if is_record_exist(key):
                        continue

                    feeds.append(
                        {
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.published,
                            "published_in_ms": get_ms(entry.published),
                        }
                    )

        self.feeds = feeds

    async def check_all(self):
        for feed in self.feeds:
            content = await scrape_body(feed["link"])

            user_prompt = f"""
            Date: {feed["published"]}
            Title: {feed["title"]}
            Link: {feed["link"]}
            Content: {content}
                        """

            system_prompt = read_news_system_prompt()

            llm = LLM()

            result = llm.complete(system_prompt, user_prompt)

            send_discord(result, "HKUST News")

            save_record(hash_string_sha256(f"RSS {feed['link']}"), True)
