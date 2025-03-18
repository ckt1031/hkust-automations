from loguru import logger

from lib.canvas.api import get_all_assignments_from_all_courses
from lib.discord_webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store

# Example of the store:
# {
#     "course_id": {
#         "assignment_id": "grade"
#     }
# }


def check_canvas_grade_changes():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")

    if webhook_url is None:
        raise ValueError(
            "DISCORD_WEBHOOK_URL_CANVAS is not provided in the environment variables"
        )

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
                f"Grade for assignment {assignment['id']} in course {course_id} has not changed ({assignment['submission']['grade']}/{assignment['points_possible']})"
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

        logger.success(
            f"Grade for assignment {assignment['id']} in course {course_id} has changed from {store[course_id][assignment['id']]} to {assignment['submission']['grade']}"
        )

        store[course_id][assignment["id"]] = assignment["submission"]["grade"]

    save_store(store_path, store)

    logger.success("Canvas Grade changes have been checked")
