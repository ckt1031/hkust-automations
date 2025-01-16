import os

import requests
from html2text import html2text
from loguru import logger
from markitdown import MarkItDown
from slugify import slugify

from canvas.api import (
    canvas_response,
    get_assignments,
    get_courses,
    get_module_items,
    get_modules,
    get_single_module_item,
)
from lib.env import getenv
from lib.openai_api import model, openai_client

headers = {
    "Authorization": f"Bearer {getenv("CANVAS_API_KEY")}",
}


def init_folder(course_id):
    if not os.path.exists(f"./dist/{course_id}"):
        os.makedirs(f"./dist/{course_id}")


def handle_text_document(path):
    md_path = ".".join(path.split(".")[:-1]) + ".md"

    if os.path.exists(md_path):
        logger.warning(f"File: {md_path} already exists")
        return

    md = MarkItDown(llm_model=model, llm_client=openai_client)
    result = md.convert(path)

    with open(md_path, "w") as f:
        f.write(result.text_content)

    os.remove(path)


def download_attachments(course_id: str, attachments: list, convert_office_pdf: bool):
    for attachment in attachments:
        url = attachment["url"]

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            raise Exception("Error fetching file", response.text)

        logger.success(f"Downloaded file: {attachment['filename']}")

        path = f"./dist/{course_id}/{attachment['filename']}"

        with open(path, "wb") as f:
            f.write(response.content)
            f.close()

        if convert_office_pdf and (
            attachment["filename"].endswith(".pdf")
            or attachment["filename"].endswith(".docx")
            or attachment["filename"].endswith(".pptx")
        ):
            handle_text_document(path)


def save_module_item(course_id, name, data):
    if len(data.strip()) == 0:
        logger.warning(f"Skipping empty module: {name}")
        return

    name = slugify(name)
    path = f"./dist/{course_id}/{name}.md"

    if os.path.exists(path):
        logger.info(f"File: {name} already exists")
        return

    with open(path, "w") as f:
        f.write(data)
        f.close()

    logger.success(f"Module Text: {name}")


def course_selector():
    logger.info("Fetching courses...")

    courses = get_courses()

    for i, course in enumerate(courses, 1):
        print(f"[{i}] {course['name'].strip()}")

    choice = input("\nEnter the number of the course you want to download: ")

    if not choice.isdigit():
        raise ValueError(f"Invalid choice: {choice}")

    choice_index = int(choice) - 1

    return (
        courses[choice_index]["id"],
        courses[choice_index]["name"],
        courses[choice_index]["course_code"],
    )


def download_canvas_files(
    course_id: str, content_id: str, convert_office_pdf: bool, download_mp4: bool
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

    url = res["url"]

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception("Error fetching file", response.text)

    logger.success(f"Downloaded file: {res['filename']}")

    with open(path, "wb") as f:
        f.write(response.content)

    if convert_office_pdf and (
        res["filename"].endswith(".pdf")
        or res["filename"].endswith(".docx")
        or res["filename"].endswith(".pptx")
    ):
        handle_text_document(path)


def download_canvas_content():
    course_id, course_name, course_code = course_selector()

    logger.info(f"Selected course: {course_name} ({course_id})")

    download_mp4 = input("Download MP4 files? (y/n): ")
    convert_office_pdf = input("Convert Office/PDF files to markdown? (y/n): ")

    download_mp4 = download_mp4.lower() == "y" or download_mp4.lower() == "yes"
    convert_office_pdf = (
        convert_office_pdf.lower() == "y" or convert_office_pdf.lower() == "yes"
    )

    modules = get_modules(course_id)

    # Create a folder for the course
    init_folder(course_id)

    for module in modules:
        for items in get_module_items(course_id, module["id"], module["items_count"]):
            if items["type"] == "Assignment":
                # Handle assignments separately
                continue

            if items["type"] == "File":
                # Run in file mode
                download_canvas_files(
                    course_id, items["content_id"], download_mp4, convert_office_pdf
                )
                continue

            if items["type"] != "Page":
                logger.warning(
                    f"Unsupported module type: {items['type']} - {items['title']}"
                )
                continue

            data = get_single_module_item(course_id, items["page_url"])

            if data is None or "body" not in data:
                continue

            save_module_item(course_id, items["title"], html2text(data["body"]))

    assignments = get_assignments(course_name, course_code, course_id)

    for assignment in assignments:
        if assignment["locked_for_user"] and "description" not in assignment:
            logger.warning(f"Assignment {assignment['id']} is locked, skipping")
            continue

        desc = html2text(assignment["description"]) if assignment["description"] else ""

        if len(desc.strip()) == 0:
            logger.warning(f"Skipping empty assignment: {assignment['name']}")
            continue

        save_module_item(course_id, assignment["name"], desc)

        if "attachments" in assignment["submission"]:
            download_attachments(
                course_id, assignment["submission"]["attachments"], convert_office_pdf
            )
