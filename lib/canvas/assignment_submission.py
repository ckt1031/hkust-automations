from datetime import datetime, timedelta, timezone

from loguru import logger

from lib.api.canvas import get_all_assignments_from_all_courses
from lib.api.discord import send_discord_webhook
from lib.api.onedrive import get_store_with_datetime, save_store_with_datetime
from lib.env import getenv


def get_assignment_submissions():
    assignments = get_all_assignments_from_all_courses()

    results = []

    for assignment in assignments:
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


def notify_incomplete_assignments():
    discord_user_id = getenv("DISCORD_USER_ID", required=True)
    webhook_url = getenv("DISCORD_WEBHOOK_CANVAS", required=True)

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

        message = f"<@{discord_user_id}>"

        send_discord_webhook(webhook_url, message=message, embed=embed)

        store[str(assignment["id"])] = datetime.now(timezone.utc)

        logger.info(f"Assignment is being checked: {assignment['id']}")

    save_store_with_datetime(store_path, store)

    logger.success("Canvas assignments submissions have been checked")
