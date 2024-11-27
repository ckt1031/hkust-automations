import sys
from datetime import datetime, timezone

from loguru import logger

import lib.env as env
from canvas.api import get_assignments, get_courses
from canvas.api_types import AssignmentListItem
from lib.notification import send_discord
from lib.onedrive_store import (
    CANVAS_ASSIGNMENT_REMINDER_PATH,
    get_record_list,
    is_recorded,
    save_record,
)
from lib.utils import get_current_iso_time


def get_assignments_for_all_courses() -> list[AssignmentListItem]:
    courses = get_courses()

    assignments: list[AssignmentListItem] = []

    for course in courses:
        course_id = str(course.id)

        course_assignments: list[AssignmentListItem] = []

        for assignment in get_assignments(course_id, only_show_upcoming=True):
            if assignment.due_at and assignment.due_at < datetime.now(timezone.utc):
                logger.debug(
                    f"Assignment {assignment.id} in course {course.id} has passed the due date, skipping"
                )
                continue

            if assignment.graded_submissions_exist:
                assignment.course_name = course.name.strip()
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

    records = get_record_list(CANVAS_ASSIGNMENT_REMINDER_PATH)
    iso_time = get_current_iso_time()

    for assignment in assignments:
        # Check if the assignment has already been recorded
        if is_recorded(records, str(assignment.id)):
            logger.debug(f"Assignment {assignment.id} was recorded, skipping")
            continue

        # Ignore if assignment has submissions
        if assignment.has_submitted_submissions:
            logger.info(f"Assignment {assignment.id} has submissions, skipping")
            continue

        message = "No expiration, but do it as soon as possible."

        if assignment.due_at is not None:
            message = f"Expiration date: `{assignment.due_at}`, <t:{int(assignment.due_at.timestamp())}:R>"

        embed = {
            "title": f"New Assignment: {assignment.name}",
            "description": message,
            "url": assignment.html_url,
            "footer": {"text": assignment.course_name},
        }

        send_discord(webhook_url, None, embed)

        logger.success(f"Assignment {assignment.id} has been sent to Discord")

        # Add the assignment to the records
        records.append({str(assignment.id): iso_time})

    save_record(CANVAS_ASSIGNMENT_REMINDER_PATH, records)

    logger.success("All assignments have been checked")
