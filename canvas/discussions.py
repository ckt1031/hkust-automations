from datetime import datetime, timezone
from time import sleep

import chevron
from html2text import html2text
from loguru import logger

from canvas.api import get_courses, get_discussion_topic_view, get_discussion_topics
from canvas.config import ENDED_COURSES
from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_schema
from prompts.canvas_discussion import DiscussionResponse, canvas_discussion_prompts


def get_replies_with_levels(view, level=0):
    output_lines = []

    for entry in view:
        if "message" not in entry:
            continue

        indent = "   " * level + "-"
        output_lines.append(f"{indent} {html2text(entry['message']).strip()}")

        if "replies" in entry and entry["replies"]:
            output_lines.extend(get_replies_with_levels(entry["replies"], level + 1))

    return output_lines


def process_conversation_data(data):
    formatted_output = []

    if "view" in data and data["view"]:
        formatted_output.extend(get_replies_with_levels(data["view"]))

    if len(formatted_output) == 0:
        return "none"

    return "\n" + "\n".join(formatted_output)


def check_discussions():
    webhook = getenv("DISCORD_WEBHOOK_URL_CANVAS_DISCUSSION")

    if webhook is None:
        logger.error("DISCORD_WEBHOOK_URL_CANVAS_DISCUSSION is not set")
        return

    courses = get_courses()

    store_path = "canvas_discussions_record.json"
    store = get_store_with_datetime(store_path)

    for course in courses:
        if course["course_code"] in ENDED_COURSES:
            logger.debug(
                f"Course {course['id']} ({course['course_code']}) is from an ended course, skipping"
            )
            continue

        logger.debug(f"Checking course {course['id']}")

        discussion_topics = get_discussion_topics(course["id"])

        pending_summarize_comments = []

        for topic in discussion_topics:
            # Skip announcements
            if topic["is_announcement"]:
                logger.debug(f"Discussion {topic['id']} is an announcement, skipping")
                continue

            if str(topic["id"]) in store:
                logger.debug(f"Discussion {topic['id']} has been recorded, skipping")
                continue

            try:
                view = get_discussion_topic_view(course["id"], topic["id"])

                comments = process_conversation_data(view)

                msg = f"ID: {topic['id']}\nTitle: {topic['title']}\nMessage: {html2text(topic['message']).strip()}"

                if comments != "none":
                    msg += f"\nComments: {comments}"

                msg += "\n\n"

                pending_summarize_comments.append(msg)
            except Exception as e:
                logger.error(f"Error processing discussion {topic['id']}: {e}")
                continue

        if len(pending_summarize_comments) == 0:
            logger.info("No discussions to summarize")
            continue

        # Run summarize, maximum 10 for each run
        for i in range(0, len(pending_summarize_comments), 10):
            chunk = pending_summarize_comments[i : i + 10]

            logger.info(f"Summarizing {len(chunk)} discussions")

            user_prompt = "\n".join(chunk)

            system_prompt = chevron.render(
                canvas_discussion_prompts,
                {"COURSE_ID": course["id"]},
            )

            res = generate_schema(system_prompt, user_prompt, DiscussionResponse)

            if res is None:
                logger.error(
                    f"Error generating schema for {course['id']} ({len(chunk)} discussions) in chunk {i / 10}"
                )
                continue

            logger.info(
                f"Generated schema for {course['id']} ({len(chunk)} discussions) in chunk {i / 10}"
            )

            ids_to_be_stored = res.accepted_ids + res.rejected_ids

            if len(ids_to_be_stored) == 0:
                logger.info(
                    f"No discussions to store for {course['id']} ({len(chunk)} discussions) in chunk {i / 10}"
                )
                continue

            for discussion in ids_to_be_stored:
                store[str(discussion)] = datetime.now(timezone.utc)

            if not res.has_summary:
                logger.warning(
                    f"No summary provided for {course['id']} ({len(chunk)} discussions) in chunk {i / 10}"
                )
                continue

            # Get course code from the course name, remove brackets and its content
            course_code: str = course["course_code"].split("(")[0].strip()

            # Discord embed
            embed = {
                "title": f"Discussions for {course_code}",
                "description": res.summary,
                "footer": {"text": course["name"].strip()},
                "color": 0xFF5DB6,
            }

            send_discord_webhook(webhook, embed=embed)

            # Save the store
            save_store_with_datetime(store_path, store)

            logger.success(
                f"Discussions for {course_code} sent to Discord successfully with {len(ids_to_be_stored)} discussions"
            )

            sleep(5)


if __name__ == "__main__":
    check_discussions()
