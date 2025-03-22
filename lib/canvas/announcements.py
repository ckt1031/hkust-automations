from datetime import datetime, timedelta, timezone

from loguru import logger

from lib.canvas.api import get_courses, get_discussion_topics
from lib.discord_webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_chat_completion
from lib.prompts.summary import summary_prompt
from lib.utils import process_html_to_text


def handle_single_announcement(course: dict, topic: dict):
    webhook = getenv("DISCORD_WEBHOOK_URL_CANVAS", required=True)

    # Convert HTML to plain text
    raw_text = process_html_to_text(topic["message"])

    content = f"Course: {course['name']}\nTitle: {topic['title']}\nContent: {raw_text}"

    llm_response = generate_chat_completion(summary_prompt, content)

    name: str = course["name"]
    course_code: str = course["course_code"]

    embed = {
        "title": f"{course_code.strip()}: {topic['title']}",
        "description": llm_response,
        "color": 0xE22928,
        "author": (
            {
                "name": topic["user_name"],
                "icon_url": (
                    topic["author"]["avatar_image_url"]
                    if topic["author"]["avatar_image_url"]
                    else None
                ),
            }
            if topic["user_name"]
            else None
        ),
        "footer": {
            "text": name.strip(),
            "timestamp": topic["posted_at"],
        },
        "url": topic["html_url"],
    }

    send_discord_webhook(webhook, embed=embed, username="Canvas")

    logger.success(f"Announcement {topic['id']} has been sent to Discord")


def notify_canvas_new_announcements():
    courses = get_courses()

    store_path = "canvas_announcement_record.json"
    store = get_store_with_datetime(store_path)

    for course in courses:
        discussion_topics = get_discussion_topics(course["id"], only_announcements=True)

        for topic in discussion_topics:
            if topic["posted_at"] is None:
                logger.warning(f"Announcement {topic['id']} has no posted_at, skipping")
                continue

            posted_at = datetime.fromisoformat(topic["posted_at"])

            # Check if the announcement has been longer than 3 days
            if posted_at < (datetime.now(timezone.utc) - timedelta(days=3)):
                logger.debug(
                    f"Announcement {topic['id']} has been posted longer than 3 days, skipping"
                )
                continue

            if str(topic["id"]) in store:
                logger.debug(f"Announcement {topic['id']} has been recorded, skipping")
                continue

            handle_single_announcement(course, topic)

            store[topic["id"]] = datetime.now(timezone.utc)

    save_store_with_datetime(store_path, store)

    logger.success("Canvas announcements have been checked")
