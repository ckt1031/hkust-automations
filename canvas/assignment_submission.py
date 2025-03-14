from datetime import datetime, timedelta, timezone

from loguru import logger

from canvas.api import get_all_assignments_from_all_courses
from canvas.config import ENDED_COURSES
from lib.discord_webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime


def get_assignment_submissions():
    assignments = get_all_assignments_from_all_courses()

    results = []

    for assignment in assignments:
        if assignment["course_code"] in ENDED_COURSES:
            logger.debug(
                f"Assignment {assignment['id']} is from an ended course, skipping"
            )
            continue

        if assignment["locked_for_user"]:
            logger.warning(f"Assignment {assignment['id']} is locked, skipping")
            continue

        # Ignore if assignment has submissions
        if assignment["has_submitted_submissions"]:
            logger.debug(f"Assignment {assignment['id']} has submissions, skipping")
            continue

        if assignment["graded_submissions_exist"]:
            logger.debug(
                f"Assignment {assignment['id']} has graded submissions, skipping"
            )
            continue

        # Check submission_types, if only ["none"] then skip
        if assignment["submission_types"] == ["none"]:
            logger.debug(
                f"Assignment {assignment['id']} has no submission types, skipping"
            )
            continue

        results.append(assignment)

    return results


def check_canvas_assignments_submissions():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")
    user_id = getenv("DISCORD_USER_ID")

    if webhook_url is None:
        raise ValueError("DISCORD_WEBHOOK_URL_CANVAS is not set")

    if user_id is None:
        raise ValueError("DISCORD_USER_ID is not set")

    assignments = get_assignment_submissions()

    store_path = "canvas_assignment_submission_reminder.json"
    store = get_store_with_datetime(store_path)

    if len(assignments) == 0:
        logger.success("No assignments to check")
        return

    for assignment in assignments:
        # No due date
        if assignment["due_at"] is None:
            logger.debug(f"Assignment {assignment['id']} has no due date, skipping")
            continue

        # Check if due date is not under 48 hours
        due_at = datetime.fromisoformat(assignment["due_at"])

        if due_at - datetime.now(timezone.utc) > timedelta(days=2):
            logger.debug(
                f"Assignment {assignment['id']} is not due within 48 hours, skipping"
            )
            continue

        if str(assignment["id"]) in store:
            logger.debug(f"Assignment {assignment['id']} was recorded, skipping")
            continue

        embed = {
            "title": f"Incomplete Assignment: {assignment['name']}",
            "description": "This assignment has not been submitted yet, please complete it before the due date.",
            "url": assignment["html_url"],
            "footer": {"text": assignment["course_name"]},
            "color": 0xFF492F,
        }

        message = f"<@{user_id}>"

        send_discord_webhook(webhook_url, message=message, embed=embed)

        store[str(assignment["id"])] = datetime.now(timezone.utc)

        logger.info(f"Assignment is being checked: {assignment['id']}")

    save_store_with_datetime(store_path, store)

    logger.success("Canvas assignments submissions have been checked")
