import requests

import lib.env as env

CANVAS_API_BASE_URL = "https://canvas.ust.hk/api"


headers = {
    "Authorization": f"Bearer {env.CANVAS_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def get_courses():
    url = f"{CANVAS_API_BASE_URL}/v1/courses"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching courses")

    return response.json()


def get_assignments(course_id: str, only_show_upcoming: bool = False):
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/assignments?order_by=due_at"

    if only_show_upcoming:
        url += "&bucket=upcoming"

    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching assignments")

    return response.json()


def get_conversations():
    url = f"{CANVAS_API_BASE_URL}/v1/conversations"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching conversations")

    return response.json()


def get_conversation_detail(conversation_id: str):
    url = f"{CANVAS_API_BASE_URL}/v1/conversations/{conversation_id}"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching conversation messages")

    return response.json()
