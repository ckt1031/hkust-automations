from loguru import logger

from canvas.api import get_assignment_groups, get_courses
from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store

# Example of the store:
# {
#     "course_id": {
#         "assignment_id": "grade"
#     }
# }


def check_grade_changes():
    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")

    if webhook_url is None:
        logger.error("No DISCORD_WEBHOOK_URL_CANVAS set")
        return

    courses = get_courses()

    store_path = "canvas_grade_changes.json"
    store = get_store(store_path)

    for course in courses:
        course_name: str = course["name"]
        course_id = str(course["id"])
        assignments_groups = get_assignment_groups(course_id)

        for group in assignments_groups:
            if group["assignments"] is None:
                logger.debug(
                    f"No assignments in group {group['id']} in course {course['id']}"
                )
                continue

            for assignment in group["assignments"]:
                assignment["id"] = str(assignment["id"])

                if (
                    assignment["submission"] is None
                    or "grade" not in assignment["submission"]
                    or assignment["submission"]["grade"] is None
                ):
                    logger.debug(
                        f"No grade for assignment {assignment['id']} in course {course['id']}"
                    )
                    continue

                # Initialize the store if it doesn't exist
                if course_id not in store:
                    store[course_id] = {}

                if assignment["id"] not in store[course_id]:
                    store[course_id][assignment["id"]] = "0"

                if (
                    store[course_id][assignment["id"]]
                    == assignment["submission"]["grade"]
                ):
                    logger.debug(
                        f"Grade for assignment {assignment['id']} in course {course['id']} has not changed ({assignment['submission']['grade']}/{assignment['points_possible']})"
                    )
                    continue

                original_field = (
                    "```diff\n- " + store[course_id][assignment["id"]] + "\n```"
                )
                new_field = "```diff\n+ " + assignment["submission"]["grade"] + "\n```"

                embed = {
                    "title": f"Grade change for {assignment['name']}",
                    "url": assignment["html_url"],
                    "fields": [
                        {
                            "name": "Original Grade",
                            "value": original_field,
                            "inline": True,
                        },
                        {"name": "Modified Grade", "value": new_field, "inline": True},
                    ],
                    "footer": {
                        "text": course_name.strip(),
                    },
                }

                send_discord_webhook(webhook_url, embed=embed, username="Canvas")

                logger.success(
                    f"Grade for assignment {assignment['id']} in course {course['id']} has changed from {store[course_id][assignment['id']]} to {assignment['submission']['grade']}"
                )

                logger.debug(
                    f"Grade for assignment {assignment['id']} is {assignment['submission']['grade']}/{assignment['points_possible']} in course {course['id']}"
                )

                store[course_id][assignment["id"]] = assignment["submission"]["grade"]

    save_store(store_path, store)
