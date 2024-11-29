from datetime import datetime, timedelta, timezone

from html2text import html2text
from loguru import logger

import lib.env as env
from canvas.api import CourseListItem, get_courses, get_discussion_topics
from canvas.api_types import DiscussionTopicListItem
from lib.llm import LLM
from lib.notification import send_discord
from lib.onedrive_store import (
    CANVAS_ANNOUNCEMENT_RECORD_PATH,
    get_record_list,
    is_recorded,
    save_record,
)
from lib.utils import get_current_iso_time
from prompts.summary import summary_prompt


def handle_single_announcement(course: CourseListItem, topic: DiscussionTopicListItem):
    webhook = env.DISCORD_WEBHOOK_URL_INBOX

    # Convert HTML to plain text
    raw_text = html2text(topic.message)

    content = f"""
        Course: {course.name}
        Title: {topic.title}
        Content: {raw_text}
    """

    llm = LLM()
    llm_response = llm.run_chat_completion(summary_prompt, content)

    embed = {
        "title": f"{course.course_code.strip()}: {topic.title}",
        "description": llm_response,
        "color": 0xE22928,
        "author": (
            {
                "name": topic.user_name,
                "icon_url": (
                    topic.author.avatar_image_url
                    if topic.author.avatar_image_url
                    else None
                ),
            }
            if topic.user_name
            else None
        ),
        "footer": {
            "text": course.name.strip(),
            "timestamp": topic.posted_at.isoformat(),
        },
        "url": topic.html_url,
    }

    send_discord(webhook, None, embed, "Canvas")

    logger.success(f"Announcement {topic.id} has been sent to Discord")


def check_canvas_announcements():
    courses = get_courses()
    records = get_record_list(CANVAS_ANNOUNCEMENT_RECORD_PATH)
    iso_time = get_current_iso_time()

    for course in courses:
        discussion_topics = get_discussion_topics(course.id, only_announcements=True)

        for topic in discussion_topics:
            # Check if the announcement has been longer than 3 days
            if topic.posted_at < (datetime.now(timezone.utc) - timedelta(days=3)):
                logger.debug(
                    f"Announcement {topic.id} has been posted longer than 3 days, skipping"
                )
                continue

            if is_recorded(records, str(topic.id)):
                logger.info(f"Announcement {topic.id} has been recorded, skipping")
                continue

            handle_single_announcement(course, topic)

            records.append({topic.id: iso_time})

    save_record(CANVAS_ANNOUNCEMENT_RECORD_PATH, records)

    logger.success("All Canvas announcements have been checked")
