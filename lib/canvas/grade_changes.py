from loguru import logger

from lib.api.canvas import get_all_assignments_from_all_courses
from lib.api.discord import send_discord_webhook
from lib.api.onedrive import get_store, save_store
from lib.env import getenv

# Example of the store:
# {
#     "course_id": {
#         "assignment_id": "grade"
#     }
# }


def notify_canvas_new_canvas_grades():
    webhook_url = getenv("DISCORD_WEBHOOK_CANVAS", required=True)

    store_path = "canvas_grade_changes.json"
    store = get_store(store_path)

    for assignment in get_all_assignments_from_all_courses():
        course_id = str(assignment["course_id"])
        course_name = assignment["course_name"]
        assignment["id"] = str(assignment["id"])

        if (
            assignment.get("submission") is None
            or "grade" not in assignment["submission"]
            or assignment["submission"]["grade"] is None
        ):
            logger.debug(
                f"No grade for assignment {assignment['id']} in course {course_id}"
            )
            continue

        # Initialize the store if it doesn't exist
        if course_id not in store:
            store[course_id] = {}

        if assignment["id"] not in store[course_id]:
            store[course_id][assignment["id"]] = "0"

        if store[course_id][assignment["id"]] == assignment["submission"]["grade"]:
            logger.debug(
                f"Assignment {assignment['id']} ({course_id}) grade has no change"
            )
            continue

        original_field = f"```diff\n- {store[course_id][assignment['id']]}\n```"
        new_field = f"```diff\n+ {assignment['submission']['grade']}\n```"

        embed = {
            "title": f"Grade change for {assignment['name']}",
            "url": assignment["html_url"],
            "fields": [
                {
                    "name": "Original",
                    "value": original_field,
                    "inline": True,
                },
                {"name": "New", "value": new_field, "inline": True},
            ],
            "footer": {
                "text": course_name,
            },
            # Green
            "color": 0x9EFE59,
        }

        send_discord_webhook(webhook_url, embed=embed, username="Canvas")

        logger.success(f"New assignment grade for {assignment['id']} ({course_id})")

        store[course_id][assignment["id"]] = assignment["submission"]["grade"]

    save_store(store_path, store)

    logger.success("Canvas Grade changes have been checked")
