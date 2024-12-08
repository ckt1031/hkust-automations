from functools import lru_cache
from urllib.parse import urlparse

import httpx

import lib.env as env
from lib.constant import HTTP_CLIENT_HEADERS


def canvas_response(path: str, params: list[tuple[str, str]] = []) -> dict:
    headers = {
        "Authorization": f"Bearer {env.CANVAS_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": HTTP_CLIENT_HEADERS["User-Agent"],
    }

    canvas_client = httpx.Client(
        http2=True,
        headers=headers,
        timeout=15,
    )

    url = f"https://canvas.ust.hk/api{path}"

    response = canvas_client.get(url, params=params)

    if response.status_code != 200:
        # Name as the suffix path, e.g. /courses
        path = urlparse(url).path
        suffix_name = path.split("/")[-1]

        raise Exception(f"Error fetching {suffix_name}")

    return response.json()


@lru_cache
def get_courses() -> list:
    return canvas_response("/v1/courses")


def get_discussion_topics(
    course_id: str, only_announcements: bool | None = None
) -> list:
    params: list[tuple[str, str]] = []

    if only_announcements is not None:
        params.append(("only_announcements", only_announcements))

    path = f"/v1/courses/{course_id}/discussion_topics"

    return canvas_response(path, params=params)


def get_discussion_topic_view(course_id: str, topic_id: str) -> dict:
    path = f"/v1/courses/{course_id}/discussion_topics/{topic_id}/view"
    return canvas_response(path)


def get_assignments(course_id: str, only_show_upcoming: bool | None = None) -> list:
    path = f"/v1/courses/{course_id}/assignments"

    params = [
        ("order_by", "due_at"),
        ("include[]", "submission"),
    ]

    if only_show_upcoming:
        params.append(("bucket", "upcoming"))

    return canvas_response(path, params=params)


def get_assignment_groups(course_id: str) -> list:
    path = f"/v1/courses/{course_id}/assignment_groups"

    params = [
        ("order_by", "due_at"),
        ("include[]", "assignments"),
        ("include[]", "submission"),
    ]

    return canvas_response(path, params=params)


def get_conversations() -> list:
    return canvas_response("/v1/conversations")


def get_conversation_detail(conversation_id: str) -> dict:
    return canvas_response(f"/v1/conversations/{conversation_id}")
