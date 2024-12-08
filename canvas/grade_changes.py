import json

import httpx
from loguru import logger

import lib.env as env
from canvas.api import get_assignment_groups, get_courses
from discord.webhook import send_discord
from lib.onedrive_store import drive_api

# Example of the store:
# {
#     "course_id": {
#         "assignment_id": "grade"
#     }
# }


def get_grade_store() -> dict[str, dict[str, str]]:
    webhook = env.DISCORD_WEBHOOK_URL_ASSIGNMENTS

    if webhook is None:
        logger.error("No DISCORD_WEBHOOK_URL_ASSIGNMENTS set")
        return

    default = {}

    response = drive_api(
        method="GET",
        path=f"{env.ONEDRIVE_STORE_FOLDER}/canvas_grade_changes.json",
    )

    if response.status_code >= 400:
        logger.error(
            f"Error getting grade store file ({response.status_code}): {response.text}"
        )
        return default

    # Get location of the file
    location = response.headers.get("Location")

    if location:
        client = httpx.Client(http2=True)
        response = client.get(location)

        if response.status_code >= 300:
            logger.error(
                f"Error getting store file ({response.status_code}): {response.text}"
            )
            return default

        data = response.json()

        logger.debug("Loaded grade store file")

        return data

    return default


def save_grade_store(store: dict[str, dict[str, str]]):
    response = drive_api(
        method="PUT",
        path=f"{env.ONEDRIVE_STORE_FOLDER}/canvas_grade_changes.json",
        data=json.dumps(store),
    )

    if response.status_code >= 300:
        logger.error(f"Error saving grade store file: {response.text}")


def check_grade_changes():
    courses = get_courses()

    store = get_grade_store()

    for course in courses:
        couse_name: str = course["name"]
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
                        "text": couse_name.strip(),
                    },
                }

                send_discord(env.DISCORD_WEBHOOK_URL_ASSIGNMENTS, None, embed, "Canvas")

                logger.success(
                    f"Grade for assignment {assignment['id']} in course {course['id']} has changed from {store[course_id][assignment['id']]} to {assignment['submission']['grade']}"
                )

                logger.debug(
                    f"Grade for assignment {assignment['id']} is {assignment['submission']['grade']}/{assignment['points_possible']} in course {course['id']}"
                )

                store[course_id][assignment["id"]] = assignment["submission"]["grade"]

    save_grade_store(store)
