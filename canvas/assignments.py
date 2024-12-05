import sys
from datetime import datetime, timezone

from loguru import logger

import lib.env as env
from canvas.api import get_assignments, get_courses
from discord.webhook import send_discord
from lib.onedrive_store import CANVAS_ASSIGNMENT_REMINDER_PATH, get_store, save_store


def get_assignments_for_all_courses() -> list:
    courses = get_courses()

    assignments = []

    for course in courses:
        course_id = str(course["id"])

        course_assignments = []

        for assignment in get_assignments(course_id, only_show_upcoming=True):
            if not assignment["due_at"]:
                logger.debug(f"Assignment {assignment['id']} has no due date, skipping")
                continue

            due_at = datetime.fromisoformat(assignment["due_at"])

            if due_at < datetime.now(timezone.utc):
                logger.debug(
                    f"Assignment {assignment['id']} has passed the due date, skipping"
                )
                continue

            if assignment["graded_submissions_exist"]:
                name: str = assignment["name"]

                assignment["course_name"] = name.strip()
                course_assignments.append(assignment)

        assignments.extend(course_assignments)

    return assignments


def check_canvas_assignments():
    webhook_url = env.DISCORD_WEBHOOK_URL_ASSIGNMENTS

    if webhook_url is None:
        logger.error(
            "Discord webhook URL is not provided in the environment variables (DISCORD_WEBHOOK_URL_ASSIGNMENTS)"
        )
        sys.exit(1)

    assignments = get_assignments_for_all_courses()

    if len(assignments) == 0:
        logger.success("No assignments to check")
        return

    store = get_store(CANVAS_ASSIGNMENT_REMINDER_PATH)

    for assignment in assignments:
        # Check if the assignment has already been recorded
        if str(assignment["id"]) in store:
            logger.debug(f"Assignment {assignment['id']} was recorded, skipping")
            continue

        # Ignore if assignment has submissions
        if assignment["has_submitted_submissions"]:
            logger.info(f"Assignment {assignment['id']} has submissions, skipping")
            continue

        message = "No expiration, but do it as soon as possible."

        if assignment["due_at"] is not None:
            due_at = datetime.fromisoformat(assignment["due_at"])

            message = f"Expiration date: `{assignment['due_at']}`, <t:{int(due_at.timestamp())}:R>"

        embed = {
            "title": f"New Assignment: {assignment['name']}",
            "description": message,
            "url": assignment["html_url"],
            "footer": {"text": assignment["course_name"]},
        }

        send_discord(webhook_url, None, embed)

        logger.success(f"Assignment {assignment['id']} has been sent to Discord")

        # Add the assignment to the records
        store[str(assignment["id"])] = datetime.now(timezone.utc)

    save_store(CANVAS_ASSIGNMENT_REMINDER_PATH, store)

    logger.success("All assignments have been checked")
