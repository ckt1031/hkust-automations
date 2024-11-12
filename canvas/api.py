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


def get_assignments(course_id: str):
    url = f"{CANVAS_API_BASE_URL}/v1/courses/{course_id}/assignments"
    response = requests.get(url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise Exception("Error fetching assignments")

    return response.json()
