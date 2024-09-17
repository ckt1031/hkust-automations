from datetime import date, timedelta

import dotenv
import feedparser
from playwright.async_api import async_playwright

from db import get_ms, hash_string_sha256, is_record_exist, save_email_record
from llm import LLM
from notification import send_discord
from utils import parse_date

dotenv.load_dotenv()

RSS_LIST = [
    "https://proxy.ckt1031.workers.dev/https://itsc.hkust.edu.hk/rss.xml",
    # "https://proxy.ckt1031.workers.dev/https://calendar.hkust.edu.hk/rss.xml",
]


def read_news_system_prompt():
    with open("prompts/news.txt", "r") as f:
        return f.read()


async def scrape_body(url):
    async with async_playwright() as p:
        # Launch a browser (you can use 'chromium', 'firefox', or 'webkit')
        browser = await p.webkit.launch()
        page = await browser.new_page()

        text_content = ""

        # Navigate to the specified URL
        await page.goto(url)

        selector_list = [".body", ".content", ".block-body"]
        for selector in selector_list:
            print(f"Fetching body for {url} with selector {selector}")
            try:
                text_content = await fetch_body(page, text_content, selector)
                break
            except Exception as e:
                print(e)
                print(f"Failed to fetch body for {url} with selector {selector}")

        # Close the browser
        await browser.close()

        return text_content


async def fetch_body(page, text_content: str, selector: str):
    # Wait for the element with class 'body' to be visible
    await page.wait_for_selector(selector)
    # Get the text content of the element
    body_content = await page.query_selector(selector)
    if body_content:
        text_content = await body_content.inner_text()
    return text_content


def get_feed(url):
    feed = feedparser.parse(url)
    return feed


class RSS:
    def __init__(self):
        feeds = []

        for rss in RSS_LIST:
            try:
                feed = get_feed(rss)

                if feed.status == 200:
                    for entry in feed.entries:
                        MAXMIUM_DAYS = 7

                        # get date of 7 days ago
                        date_of_max_days = date.today() - timedelta(days=MAXMIUM_DAYS)

                        if parse_date(entry.published).date() < date_of_max_days:
                            print(
                                f"Skipping RSS feed {entry.link} as it is older than {MAXMIUM_DAYS} days"
                            )
                            continue

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
            except Exception as e:
                print(f"Error in fetching RSS feed {rss}: {e}")

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

            save_email_record(hash_string_sha256(f"RSS {feed['link']}"), True)
