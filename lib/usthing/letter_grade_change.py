from loguru import logger

from lib.discord_webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store
from lib.usthing.api import get_course_grades


def notify_letter_grade_change():
    data = get_course_grades()

    store_path = "letter_grade_change.json"
    store = get_store(store_path)

    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")

    if webhook_url is None:
        raise ValueError(
            "DISCORD_WEBHOOK_URL_CANVAS is not provided in the environment variables"
        )

    grades = data["stdtInfo"][0]["stdtCourseGrade"]

    if len(grades) == 0:
        logger.success("No grades to check")
        return

    for grade_data in grades:
        courseGrade: str = grade_data["crseGrade"]
        courseCode: str = grade_data["crseCode"]
        grade_letter = courseGrade.strip()
        key = grade_data["crseTakenTerm"] + "-" + courseCode

        if grade_letter == "":
            logger.warning(f"{courseCode} has no grade, skipping")
            continue

        if store.get(key) is not None and store[key] == grade_letter:
            logger.debug(f"Grade for {courseCode} is recorded, skipping")
            continue

        logger.success(f"New grade for {courseCode} is found")

        store[key] = grade_letter

        send_discord_webhook(
            webhook_url,
            message=f"Grade for **{courseCode}** has set to `{grade_letter}`",
        )

    save_store(store_path, store)

    logger.success("USTHing letter grade check completed")
