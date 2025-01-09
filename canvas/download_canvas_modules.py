import os

import requests
from html2text import html2text
from loguru import logger
from markitdown import MarkItDown
from slugify import slugify

from canvas.api import (
    canvas_response,
    get_courses,
    get_module_items,
    get_modules,
    get_single_module_item,
)
from lib.env import getenv
from lib.openai_api import openai_client


def init_folder(course_id):
    if not os.path.exists(f"./dist/{course_id}"):
        os.makedirs(f"./dist/{course_id}")


def save_module_item(course_id, name, data):
    name = slugify(name)
    path = f"./dist/{course_id}/{name}.md"

    if os.path.exists(path):
        logger.warning(f"File: {name} already exists")
        return

    with open(path, "w") as f:
        f.write(data)


def course_selector():
    logger.info("Fetching courses...")

    courses = get_courses()

    for i, course in enumerate(courses, 1):
        print(f"[{i}] {course['name'].strip()}")

    choice = input("\nEnter the number of the course you want to download: ")

    if not choice.isdigit():
        raise ValueError(f"Invalid choice: {choice}")

    choice_index = int(choice) - 1

    return courses[choice_index]["id"]


def download_canvas_files(
    course_id: str, content_id: str, llm_model: str, download_mp4: bool
):
    res = canvas_response(f"/courses/{course_id}/files/{content_id}")

    if not res:
        raise Exception(
            f"Failed to download file: {content_id} from course: {course_id}"
        )

    path = f"./dist/{course_id}/{res['filename']}"

    if not download_mp4 and res["filename"].endswith(".mp4"):
        logger.warning(f"Skipping: {res['filename']} as it is an MP4 file")
        return

    # Check if file exists
    if os.path.exists(path):
        logger.warning(f"File: {res['filename']} already exists")
        return

    CANVAS_API_KEY = getenv("CANVAS_API_KEY")

    headers = {
        "Authorization": f"Bearer {CANVAS_API_KEY}",
    }

    url = res["url"]

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception("Error fetching file", response.text)

    logger.success(f"Downloaded file: {res['filename']}")

    with open(path, "wb") as f:
        f.write(response.content)

    if (
        res["filename"].endswith(".pdf")
        or res["filename"].endswith(".docx")
        or res["filename"].endswith(".pptx")
    ):
        md_path = ".".join(path.split(".")[:-1]) + ".md"

        if os.path.exists(md_path):
            logger.warning(f"File: {md_path} already exists")
            return

        md = MarkItDown(llm_model=llm_model, llm_client=openai_client)
        result = md.convert(path)

        with open(md_path, "w") as f:
            f.write(result.text_content)
            logger.success(f"Converted file: {res["filename"]}")

        os.remove(path)


def download_canvas_modules():
    course_id = course_selector()
    llm_model = input("Enter the LLM model: ")
    download_mp4 = input("Download MP4 files? (y/n): ")

    download_mp4 = download_mp4.lower() == "y" or download_mp4.lower() == "yes"

    modules = get_modules(course_id)

    init_folder(course_id)

    for module in modules:
        for items in get_module_items(course_id, module["id"], module["items_count"]):
            if items["type"] == "File":
                # Run in file mode
                download_canvas_files(
                    course_id, items["content_id"], llm_model, download_mp4
                )
                continue

            if items["type"] != "Page":
                logger.warning(f"Skipping: {items['title']} as it is not a Page")
                continue

            data = get_single_module_item(course_id, items["page_url"])

            if data is None or "body" not in data:
                continue

            save_module_item(course_id, items["title"], html2text(data["body"]))
            logger.success(f"Module Text: {items['title']}")

    pass
