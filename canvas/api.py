from functools import lru_cache

import httpx

import lib.env as env
from lib.constant import HTTP_CLIENT_HEADERS

CANVAS_API_BASE_URL = "https://canvas.ust.hk/api"


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


@lru_cache
def get_courses() -> list:
    url = f"{CANVAS_API_BASE_URL}/v1/courses"
    response = canvas_client.get(url)

    if response.status_code != 200:
        raise Exception("Error fetching courses")

    return response.json()


def get_discussion_topics(
    course_id: str, only_announcements: bool | None = None
) -> list:
    params = []

    if only_announcements is not None:
        params.append(("only_announcements", only_announcements))

    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/discussion_topics"
    response = canvas_client.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Error fetching discussion topics")

    return response.json()


def get_discussion_topic_view(course_id: str, topic_id: str) -> dict:
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/discussion_topics/{topic_id}/view"
    response = canvas_client.get(url)

    if response.status_code != 200:
        raise Exception("Error fetching discussion topic view")

    return response.json()


def get_assignments(course_id: str, only_show_upcoming: bool | None = None) -> list:
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/assignments"

    params = [
        ("order_by", "due_at"),
        ("include[]", "submission"),
    ]

    if only_show_upcoming:
        params.append(("bucket", "upcoming"))

    response = canvas_client.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Error fetching assignments")

    return response.json()


def get_assignment_groups(course_id: str) -> list:
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/assignment_groups"

    params = [
        ("order_by", "due_at"),
        ("include[]", "assignments"),
        ("include[]", "submission"),
    ]

    response = canvas_client.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Error fetching assignments")

    return response.json()


def get_conversations() -> list:
    url = f"{CANVAS_API_BASE_URL}/v1/conversations"
    response = canvas_client.get(url)

    if response.status_code != 200:
        raise Exception("Error fetching conversations")

    return response.json()


def get_conversation_detail(conversation_id: str) -> dict:
    url = f"{CANVAS_API_BASE_URL}/v1/conversations/{conversation_id}"
    response = canvas_client.get(url)

    if response.status_code != 200:
        raise Exception("Error fetching conversation messages")

    return response.json()
