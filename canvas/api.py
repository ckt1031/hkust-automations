from functools import lru_cache

import msgspec
import requests

import lib.env as env
from canvas.api_types import (
    AssignmeGroupItem,
    AssignmentListItem,
    ConversationsDetail,
    ConversationsListItem,
    CourseListItem,
    DiscussionTopicItemView,
    DiscussionTopicListItem,
)
from lib.constant import HTTP_CLIENT_HEADERS

CANVAS_API_BASE_URL = "https://canvas.ust.hk/api"


headers = {
    "Authorization": f"Bearer {env.CANVAS_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": HTTP_CLIENT_HEADERS["User-Agent"],
}


@lru_cache
def get_courses() -> list[CourseListItem]:
    url = f"{CANVAS_API_BASE_URL}/v1/courses"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching courses")

    return msgspec.json.decode(response.text, type=list[CourseListItem])


def get_discussion_topics(
    course_id: str, only_announcements: bool | None = None
) -> list[DiscussionTopicListItem]:
    params = []

    if only_announcements is not None:
        params.append(("only_announcements", only_announcements))

    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/discussion_topics"
    response = requests.get(url, headers=headers, timeout=15, params=params)

    if response.status_code != 200:
        raise Exception("Error fetching discussion topics")

    return msgspec.json.decode(response.text, type=list[DiscussionTopicListItem])


def get_discussion_topic_view(course_id: str, topic_id: str) -> DiscussionTopicItemView:
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/discussion_topics/{topic_id}/view"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching discussion topic view")

    return msgspec.json.decode(response.text, type=DiscussionTopicItemView)


def get_assignments(
    course_id: str, only_show_upcoming: bool | None = None
) -> list[AssignmentListItem]:
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/assignments"

    params = [
        ("order_by", "due_at"),
        ("include[]", "submission"),
    ]

    if only_show_upcoming:
        params.append(("bucket", "upcoming"))

    response = requests.get(url, headers=headers, timeout=5, params=params)

    if response.status_code != 200:
        raise Exception("Error fetching assignments")

    return msgspec.json.decode(response.text, type=list[AssignmentListItem])


def get_assignment_groups(course_id: str) -> list[AssignmeGroupItem]:
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/assignment_groups"

    params = [
        ("order_by", "due_at"),
        ("include[]", "assignments"),
        ("include[]", "submission"),
    ]

    response = requests.get(url, headers=headers, timeout=5, params=params)

    if response.status_code != 200:
        raise Exception("Error fetching assignments")

    return msgspec.json.decode(response.text, type=list[AssignmeGroupItem])


def get_conversations() -> list[ConversationsListItem]:
    url = f"{CANVAS_API_BASE_URL}/v1/conversations"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching conversations")

    return msgspec.json.decode(response.text, type=list[ConversationsListItem])


def get_conversation_detail(conversation_id: str) -> ConversationsDetail:
    url = f"{CANVAS_API_BASE_URL}/v1/conversations/{conversation_id}"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching conversation messages")

    return msgspec.json.decode(response.text, type=ConversationsDetail)
