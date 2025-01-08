from datetime import datetime, timezone
from time import sleep

from bs4 import BeautifulSoup
from loguru import logger

from browser.chrome import get_driver
from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from prompts.reddit import RedditMassPostsResponse, reddit_prompts
from rss.news import exceed_maximum_check_days
from rss.utils import parse_rss_feed


def remove_excessive_whitespace(text):
    return " ".join(text.split())


def scrape_reddit(driver, link: str) -> dict[str] or None:
    import undetected_chromedriver as Chrome

    driver: Chrome = driver

    driver.get(link)

    # Wait for the page to load
    driver.implicitly_wait(5)

    # Scroll down to load comments
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(2)

    # Obtain page source
    html = driver.page_source

    # Get <shreddit-post> elements
    bs = BeautifulSoup(html, "html.parser")

    # Get the post
    post = bs.find("shreddit-post")

    if post is None:
        logger.info(f"No post found: {link}")
        return

    content = ""
    comments = ""

    # content is under text-neutral-content div tag
    content_element = post.find("div", class_="text-neutral-content")

    if content_element is not None:
        content = content_element.text.replace("Read more", "").strip()

    # Get Multiple shreddit-comment
    shreddit_comment = bs.find_all("shreddit-comment")

    if shreddit_comment is not None:
        for comment in shreddit_comment:
            # Assuming the text is within a <p> tag inside each 'shreddit-comment'
            comment_text = comment.find("p").get_text() if comment.find("p") else ""
            comments += comment_text + "\n"

    return {
        "title": driver.title.replace(" : r/HKUST", ""),
        "content": remove_excessive_whitespace(content),
        "comments": remove_excessive_whitespace(comments),
    }


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

    driver = get_driver()

    scraped_reddit = []

    store_path = "reddit.json"
    store = get_store_with_datetime(store_path)

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

        logger.debug(f"Checking Reddit - {entry.link}")

        # Extract the website
        data = scrape_reddit(driver, entry.link)

        if data is None:
            continue

        logger.success(f"Scraped Reddit - {data['title']}")

        scraped_reddit.append({**data, "link": entry.link})

    # Chunk into 5 and analyze
    for i in range(0, len(scraped_reddit), 5):
        user_prompt = f"Reddit Analysis - {i + 1} to {i + 5}\n\n"
        for data in scraped_reddit[i : i + 5]:
            _id = (
                data["link"]
                .replace("https://www.reddit.com/r/HKUST/comments/", "")
                .split("/")[0]
            )

            user_prompt += f"Title: {data['title']}\n"
            user_prompt += f"ID: {_id}\n"
            user_prompt += f"Content: {data['content']}\n"
            user_prompt += f"Comments: {data['comments']}\n\n"

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
            logger.info(f"Summary: {res.summary}")

            discord_embed = {
                "title": "Reddit Summary",
                "description": res.summary,
                # Red
                "color": 0xFF0000,
            }

            send_discord_webhook(webhook, embed=discord_embed, username="HKUST Reddit")

        save_store_with_datetime(store_path, store)

        logger.success(f"Analyzed Reddit - {i + 1} to {i + 5}")

    try:
        driver.quit()
    except Exception as e:
        logger.error(f"Failed to quit driver: {e}")
