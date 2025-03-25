from datetime import datetime, timezone

from loguru import logger

from lib.canvas.api import get_all_assignments_from_all_courses
from lib.discord_webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_chat_completion
from lib.prompts import summary
from lib.utils import process_html_to_text


def notify_canvas_new_assignments():
    webhook_url = getenv("DISCORD_WEBHOOK_CANVAS", required=True)

    assignments = get_all_assignments_from_all_courses()

    if len(assignments) == 0:
        logger.success("No assignments to check")
        return

    store_path = "canvas_assignment_reminder.json"
    store = get_store_with_datetime(store_path)

    for assignment in assignments:
        # Check if the assignment has already been recorded
        if str(assignment["id"]) in store:
            logger.debug(f"Assignment {assignment['id']} was recorded, skipping")
            continue

        # Ignore if assignment has submitted submissions
        if assignment["has_submitted_submissions"]:
            logger.debug(f"Assignment {assignment['id']} has submissions, skipping")
            continue

        # Check submission_types, if only ["none"] then skip
        if assignment["submission_types"] == ["none"]:
            logger.debug(
                f"Assignment {assignment['id']} has no submission types, skipping"
            )
            continue

        if assignment["locked_for_user"]:
            logger.warning(f"Assignment {assignment['id']} is locked, skipping")
            continue

        embed = {
            "title": f"New Assignment: {assignment['name']}",
            "url": assignment["html_url"],
            "footer": {"text": assignment["course_name"]},
            "color": 0x93B6FF,
        }

        if assignment["due_at"] is not None:
            due_at = datetime.fromisoformat(assignment["due_at"])

            if due_at < datetime.now(timezone.utc):
                logger.debug(
                    f"Assignment {assignment['id']} has passed the due date, skipping"
                )
                continue

            date_time_str = due_at.strftime("%Y-%m-%d %H:%M:%S")

            embed["fields"] = [
                {
                    "name": "Due Date",
                    "value": date_time_str + f" (<t:{int(due_at.timestamp())}:R>)",
                    "inline": True,
                }
            ]

        if (
            assignment["description"] is not None
            and len(assignment["description"].strip()) > 0
        ):
            assignment["description"] = process_html_to_text(assignment["description"])
            user_prompt = f"Name: {assignment['name']}\nCourse: {assignment['course_name']}\nDescription: {assignment['description']}"

            llm_response = generate_chat_completion(
                summary.summary_prompt, user_prompt
            ).strip()
            embed["description"] = llm_response

        send_discord_webhook(webhook_url, embed=embed)

        logger.success(f"Assignment {assignment['id']} has been sent to Discord")

        # Add the assignment to the records
        store[str(assignment["id"])] = datetime.now(timezone.utc)

    save_store_with_datetime(store_path, store)

    logger.success("Canvas assignments have been checked")
