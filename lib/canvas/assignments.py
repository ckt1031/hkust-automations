from datetime import datetime, timezone

from loguru import logger

from lib.api.canvas import get_all_assignments_from_all_courses
from lib.api.discord import send_discord_webhook
from lib.api.microsoft import MicrosoftGraphAPI
from lib.api.openai import generate_chat_completion, generate_schema
from lib.env import getenv
from lib.onedrive_store import get_store_with_datetime, save_store_with_datetime
from lib.prompts import canvas_assigmnet_todo, summary
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

        # Check submission_types, if only ["none"] or only ["on_paper"] then skip
        if assignment["submission_types"] == ["none"] or assignment[
            "submission_types"
        ] == ["on_paper"]:
            logger.debug(
                f"Assignment {assignment['id']} has no uploadable submission types, skipping"
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

        # Prepare LLM prompt to check if should add to Todo
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        user_prompt = f"""
Assignment Name: {assignment['name']}
Course Name: {assignment['course_name']}
Submission Types: {','.join(assignment['submission_types'])}
Due Date: {assignment['due_at'] if assignment['due_at'] else 'None'}
Description: {assignment['description'] if assignment['description'] else 'None'}
Today's Date: {today}
"""

        # Check with LLM if should add to Todo
        try:
            todo_check = generate_schema(
                canvas_assigmnet_todo.canvas_assignment_todo_prompts,
                user_prompt,
                canvas_assigmnet_todo.CanvasAssignmentTodoSchema,
            )

            # If validated, add to Microsoft Todo
            if not todo_check.satisfied:
                logger.debug(
                    f"Assignment {assignment['id']} is not satisfied for Todo, skipping"
                )
                continue

            ms_api = MicrosoftGraphAPI()

            # Get the Microsoft Todo list ID by displayName "📕 Homework"
            todo_lists = ms_api.list_tasks_lists()

            todo_list_id = None

            for todo_list in todo_lists:
                if todo_list["displayName"] == "📕 Homework":
                    todo_list_id = todo_list["id"]
                    break

            if todo_list_id is None:
                logger.error("Todo list not found")
                continue

            # Create a new task in Microsoft Todo
            ms_api.create_todo_task(
                title=todo_check.name,
                list_id=todo_list_id,
                due_date=todo_check.task_due,
            )
            logger.success(f"Added assignment {assignment['id']} to Microsoft Todo")
        except Exception as e:
            logger.error(
                f"Error processing Todo for assignment {assignment['id']}: {e}"
            )

        logger.success(f"Assignment {assignment['id']} has been sent to Discord")

        # Add the assignment to the records
        store[str(assignment["id"])] = datetime.now(timezone.utc)

    save_store_with_datetime(store_path, store)

    logger.success("Canvas assignments have been checked")
