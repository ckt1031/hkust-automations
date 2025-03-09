import os

import requests
from html2text import html2text
from loguru import logger
from mistralai import Mistral
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
from lib.openai_api import generate_chat_completion

headers = {
    "Authorization": f"Bearer {getenv("CANVAS_API_KEY")}",
}


def init_folder(course_code):
    if not os.path.exists(f"./dist/{course_code}"):
        os.makedirs(f"./dist/{course_code}")

    # Add Markdown and Files folder
    if not os.path.exists(f"./dist/{course_code}/Markdown"):
        os.makedirs(f"./dist/{course_code}/Markdown")

    if not os.path.exists(f"./dist/{course_code}/Files"):
        os.makedirs(f"./dist/{course_code}/Files")


def handle_text_document(file_name: str, path: str):
    md_path = ".".join(path.split(".")[:-1]) + ".md"

    if os.path.exists(md_path):
        logger.warning(f"File: {md_path} already exists")
        return

    api_key = getenv("MISTRAL_API_KEY")

    client = Mistral(api_key=api_key)

    uploaded_pdf = client.files.upload(
        file={
            "file_name": file_name,
            "content": open(path, "rb"),
        },
        purpose="ocr",
    )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=False,
    )

    text = ""

    for page in ocr_response.pages:
        text += page.markdown

    final_text = generate_chat_completion(
        system_message="""
        Your task is to finalize and clean up the markdown which is generated from the OCR process and extract the text from the document.
        Please remove any unnecessary text, and ensure that the markdown is clean and readable.
        Format the text in a way that it is easy to read and understand.
        """,
        user_message=text,
    )

    with open(md_path, "w") as f:
        f.write(final_text)
        f.close()


def download_attachments(course_code: str, attachments: list, convert_office_pdf: bool):
    for attachment in attachments:
        url = attachment["url"]
        path = f"./dist/{course_code}/Files/{attachment['filename']}"

        # Check if the Markdown file was handled
        md_path = ".".join(path.split(".")[:-1]) + ".md"
        if os.path.exists(md_path):
            logger.warning(f"File: {md_path} already exists")
            return

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            raise Exception("Error fetching file", response.text)

        logger.success(f"Downloaded file: {attachment['filename']}")

        with open(path, "wb") as f:
            f.write(response.content)
            f.close()

        if convert_office_pdf and (
            attachment["filename"].endswith(".pdf")
            or attachment["filename"].endswith(".docx")
            or attachment["filename"].endswith(".pptx")
        ):
            handle_text_document(
                attachment["filename"],
                f"./dist/{course_code}/Markdown/{attachment['filename']}",
            )


def save_module_item(course_code: str, name: str, data: str):
    if len(data.strip()) == 0:
        logger.warning(f"Skipping empty module: {name}")
        return

    name = slugify(name)
    path = f"./dist/{course_code}/Markdown/{name}.md"

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
    course_id: str, course_code: str, content_id: str, convert_office_pdf: bool
):
    res = canvas_response(f"/courses/{course_id}/files/{content_id}")

    if not res:
        raise Exception(
            f"Failed to download file: {content_id} from course: {course_id}"
        )

    path = f"./dist/{course_code}/Files/{res['filename']}"

    # Check if a file exists
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
        handle_text_document(res["filename"], path)


def download_canvas_content():
    course_id, course_name, course_code = course_selector()

    logger.info(f"Selected course: {course_name} ({course_id})")

    convert_office_pdf = input("Convert Office/PDF files to markdown? (y/n): ")

    convert_office_pdf = (
        convert_office_pdf.lower() == "y" or convert_office_pdf.lower() == "yes"
    )

    modules = get_modules(course_id)

    # Create a folder for the course
    init_folder(course_code)

    for module in modules:
        for items in get_module_items(course_id, module["id"], module["items_count"]):
            if items["type"] == "Assignment":
                # Handle assignments separately
                continue

            if items["type"] == "File":
                # Run in file mode
                download_canvas_files(
                    course_id,
                    course_code,
                    items["content_id"],
                    convert_office_pdf,
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

            # Use LLM to generate content
            text_body = generate_chat_completion(
                system_message="""
                Extract the text from the Canvas page and format it in a way that is easy to read and understand.
                The content should be clean and readable.
                The original version could be HTML, so make sure to convert it to markdown.
                Your task is to finalize and clean up the markdown which is generated from the Canvas page.
                """,
                user_message=data["body"],
            )

            save_module_item(course_code, items["title"], text_body)

    assignments = get_assignments(course_name, course_code, course_id)

    for assignment in assignments:
        if assignment["locked_for_user"] and "description" not in assignment:
            logger.warning(f"Assignment {assignment['id']} is locked, skipping")
            continue

        desc = html2text(assignment["description"]) if assignment["description"] else ""

        if len(desc.strip()) == 0:
            logger.warning(f"Skipping empty assignment: {assignment['name']}")
            continue

        save_module_item(course_code, assignment["name"], desc)

        if "attachments" in assignment["submission"]:
            download_attachments(
                course_code,
                assignment["submission"]["attachments"],
                convert_office_pdf,
            )
