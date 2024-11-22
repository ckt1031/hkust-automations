import sys
from datetime import datetime, timezone

from loguru import logger

import lib.env as env
from canvas.api import get_assignments, get_courses
from lib.notification import send_discord
from lib.onedrive_store import (
    CANVAS_ASSIGNMENT_REMINDER_PATH,
    get_record,
    is_recorded,
    save_record,
)
from lib.utils import get_current_iso_time


def is_after_due_date(due_at: str) -> bool:
    # due_at is in ISO 8601 format
    # If the due date is not set, return False

    if due_at is None:
        return False

    # Parse the due_at string to a datetime object
    due_date = datetime.fromisoformat(due_at)

    # Ensure due_date is timezone-aware
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    # Get the current time in UTC
    now = datetime.now(timezone.utc)

    # If the due date is in the past, return True
    return due_date < now


def get_assignments_for_all_courses():
    courses = get_courses()

    assignments = []

    for course in courses:
        course_id = str(course["id"])

        course_assignments = []

        for assignment in get_assignments(course_id, only_show_upcoming=True):
            if is_after_due_date(assignment["due_at"]):
                logger.info(
                    f"Assignment {assignment['id']} in course {course['id']} has passed the due date, skipping"
                )
                continue

            if (
                # not assignment["has_submitted_submissions"]
                not assignment["graded_submissions_exist"]
            ):
                assignment["course_name"] = course["name"].strip()
                course_assignments.append(assignment)

        assignments.extend(course_assignments)

    return assignments


def format_iso_date(date: str) -> str:
    # Parse the input date string to a datetime object 2024-12-31T04:00:00Z
    parsed_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")

    # Format the datetime object to ISO 8601 format
    iso_date = parsed_date.strftime("%Y-%m-%d")

    return iso_date


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

    records = get_record(CANVAS_ASSIGNMENT_REMINDER_PATH)
    iso_time = get_current_iso_time()

    for assignment in assignments:
        # Check if the assignment has already been recorded
        if is_recorded(records, str(assignment["id"])):
            logger.info(f"Assignment {assignment['id']} was recorded, skipping")
            continue

        message = "No expiration, but do it as soon as possible."

        if assignment["due_at"] is not None:
            due_time = datetime.fromisoformat(assignment["due_at"])
            date_str = format_iso_date(assignment["due_at"])
            message = (
                f"Expiration date: `{date_str}`, <t:{int(due_time.timestamp())}:R>"
            )

        embed = {
            "title": f"New Assignment: {assignment['name']}",
            "description": message,
            "url": assignment["html_url"],
            "footer": {"text": assignment["course_name"]},
        }

        send_discord(webhook_url, None, embed)

        logger.success(f"Assignment {assignment['id']} has been sent to Discord")

        # Add the assignment to the records
        records.append({str(assignment["id"]): iso_time})

    save_record(CANVAS_ASSIGNMENT_REMINDER_PATH, records)

    logger.success("All assignments have been checked")
