from functools import cache
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed

from lib.env import getenv

load_dotenv()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def canvas_response(path: str, params=None) -> dict | list:
    if params is None:
        params = []

    CANVAS_API_KEY = getenv("CANVAS_API_KEY")

    headers = {
        "Authorization": f"Bearer {CANVAS_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = f"https://canvas.ust.hk/api/v1{path}"

    response = requests.get(url, params=params, headers=headers, timeout=15)

    if response.status_code != 200:
        # Name as the suffix path, e.g. /courses
        path = urlparse(url).path
        suffix_name = path.split("/")[-1]

        raise Exception(f"Error fetching {suffix_name}", response.text)

    return response.json()


@cache
def get_courses() -> list:
    response: list[dict] = canvas_response("/courses")

    courses = []

    for course in response:
        # If course has access_restricted_by_date=True, skip
        if course.get("access_restricted_by_date") is True:
            logger.debug(f"Course {course['id']} is restricted by date")
            continue

        courses.append(course)

    return courses


@cache
def get_discussion_topics(
    course_id: str, only_announcements: bool | None = None
) -> list:
    params: list[tuple[str, str | bool]] = []

    if only_announcements is not None:
        params.append(("only_announcements", only_announcements))

    path = f"/courses/{course_id}/discussion_topics"

    return canvas_response(path, params=params)


@cache
def get_discussion_topic_data(course_id: str, topic_id: str) -> dict:
    path = f"/courses/{course_id}/discussion_topics/{topic_id}"
    return canvas_response(path)


@cache
def get_discussion_topic_view(course_id: str, topic_id: str) -> dict:
    path = f"/courses/{course_id}/discussion_topics/{topic_id}/view"
    return canvas_response(path)


@cache
def get_assignment_groups(course_id: str) -> list:
    path = f"/courses/{course_id}/assignment_groups"

    params = [
        ("order_by", "due_at"),
        ("include[]", "assignments"),
        ("include[]", "submission"),
    ]

    return canvas_response(path, params=params)


@cache
def get_all_assignments_from_all_courses():
    courses = get_courses()

    assignments = []

    for course in courses:
        course_name: str = course["name"]
        course_id = str(course["id"])
        assignments_groups = get_assignment_groups(course_id)

        for group in assignments_groups:
            if group["assignments"] is None:
                continue

            for assignment in group["assignments"]:
                assignment["id"] = str(assignment["id"])
                assignment["name"] = assignment["name"].strip()
                assignment["course_name"] = course_name.strip()

                assignments.append(assignment)

    return assignments


@cache
def get_conversations() -> list[dict]:
    return canvas_response("/conversations")


@cache
def get_conversation_detail(conversation_id: str) -> dict:
    return canvas_response(f"/conversations/{conversation_id}")
