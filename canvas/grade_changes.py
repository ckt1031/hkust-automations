import msgspec
from loguru import logger

import lib.env as env
from canvas.api import get_assignment_groups, get_courses
from lib.notification import send_discord
from lib.onedrive_store import STORE_FOLDER, drive_api, save_record

# {
#     "course_id": {
#         "assignment_id": "grade"
#     }
# }

CANVAS_GRADE_CHANGES_PATH = f"{STORE_FOLDER}/grade_changes.json"


def get_grade_record(path: str) -> dict[str, dict[int, str]]:
    webhook = env.DISCORD_WEBHOOK_URL_ASSIGNMENTS

    if webhook is None:
        logger.error("No DISCORD_WEBHOOK_URL_ASSIGNMENTS set")
        return

    default = {}

    response = drive_api(method="GET", path=path)

    if response.status_code != 200:
        logger.error(f"Error getting grade store file: {response.text}")
        return default

    return msgspec.json.decode(response.text, type=dict[str, dict[int, str]])


def check_grade_changes():
    courses = get_courses()

    record = get_grade_record(CANVAS_GRADE_CHANGES_PATH)

    for course in courses:
        course.name = course.name.strip()

        course_id = str(course.id)
        assignments_groups = get_assignment_groups(course_id)

        for group in assignments_groups:
            if group.assignments is None:
                logger.debug(
                    f"No assignments in group {group.id} in course {course.id}"
                )
                continue

            for assignment in group.assignments:
                if assignment.submission is None:
                    logger.debug(
                        f"No submission for assignment {assignment.id} in course {course.id}"
                    )
                    continue

                if assignment.submission.grade is None:
                    logger.debug(
                        f"No grade for assignment {assignment.id} in course {course.id}"
                    )
                    continue

                if (
                    record.get(course_id, {}).get(assignment.id)
                    == assignment.submission.grade
                ):
                    logger.debug(
                        f"Grade for assignment {assignment.id} in course {course.id} has not changed"
                    )
                    continue

                record.setdefault(course_id, {})[assignment.id] = (
                    record[course_id][assignment.id]
                    if record.get(course_id, {}).get(assignment.id)
                    else "0"
                )

                original_field = (
                    "```diff\n- " + record[course_id][assignment.id] + "\n```"
                )
                new_field = "```diff\n+ " + assignment.submission.grade + "\n```"

                embed = {
                    "title": f"Grade change for {assignment.name}",
                    "url": assignment.html_url,
                    "fields": [
                        {
                            "name": "Original Grade",
                            "value": original_field,
                            "inline": True,
                        },
                        {"name": "Modified Grade", "value": new_field, "inline": True},
                    ],
                    "footer": {"text": course.name},
                }

                send_discord(env.DISCORD_WEBHOOK_URL_ASSIGNMENTS, None, embed, "Canvas")

                logger.success(
                    f"Grade for assignment {assignment.id} in course {course.id} has changed from {record[course_id][assignment.id]} to {assignment.submission.grade}"
                )

                logger.debug(
                    f"Grade for assignment {assignment.id} is {assignment.submission.grade}/{assignment.points_possible} in course {course.id}"
                )

                record.setdefault(course_id, {})[
                    (assignment.id)
                ] = assignment.submission.grade

    save_record(CANVAS_GRADE_CHANGES_PATH, record)
