from datetime import datetime, timezone

from html2text import html2text
from loguru import logger

from canvas.api import get_all_assignments_from_all_courses
from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.openai_api import generate_chat_completion
from prompts import summary


def check_canvas_assignments():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")

    if webhook_url is None:
        raise ValueError(
            "DISCORD_WEBHOOK_URL_CANVAS is not provided in the environment variables"
        )

    assignments = get_all_assignments_from_all_courses()

    if len(assignments) == 0:
        logger.success("No assignments to check")
        return

    store_path = "canvas_assignment_reminder.json"
    store = get_store_with_datetime(store_path)

    for assignment in assignments:
        if not assignment["graded_submissions_exist"]:
            logger.debug(f"Assignment {assignment['id']} has no graded submissions")
            continue

        # Check if the assignment has already been recorded
        if str(assignment["id"]) in store:
            logger.debug(f"Assignment {assignment['id']} was recorded, skipping")
            continue

        # Ignore if assignment has submissions
        if assignment["has_submitted_submissions"]:
            logger.info(f"Assignment {assignment['id']} has submissions, skipping")
            continue

        # PHYS1112
        if (
            "not graded" in assignment["name"].lower()
            or "tutorial" in assignment["name"].lower()
        ):
            logger.debug(f"Assignment {assignment['id']} will not be graded, skipping")
            continue

        embed = {
            "title": f"New Assignment: {assignment['name']}",
            "url": assignment["html_url"],
            "footer": {"text": assignment["course_name"]},
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

        if assignment["description"] is not None:
            assignment["description"] = html2text(assignment["description"])
            user_prompt = f"Name: {assignment['name']}\nCourse: {assignment['course_name']}\nDescription: {assignment['description']}"

            llm_response = generate_chat_completion(
                summary.summary_prompt, user_prompt
            ).strip()
            embed["description"] = llm_response

            print(llm_response)

        send_discord_webhook(webhook_url, embed=embed)

        logger.success(f"Assignment {assignment['id']} has been sent to Discord")

        # Add the assignment to the records
        store[str(assignment["id"])] = datetime.now(timezone.utc)

    save_store_with_datetime(store_path, store)

    logger.success("All assignments have been checked")
