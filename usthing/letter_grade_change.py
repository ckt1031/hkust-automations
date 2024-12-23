from loguru import logger

from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store
from usthing.api import get_course_grades


def check_letter_grade_change():
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
        crseGrade: str = grade_data["crseGrade"]
        grade_letter = crseGrade.strip()
        key = grade_data["crseTakenTerm"] + "-" + grade_data["crseCode"]

        if grade_letter == "":
            logger.warning(f"No grade for {grade_data['crseCode']}, skipping")
            continue

        if store.get(key) is None or store[key] != grade_letter:
            logger.success(
                f"Grade for {grade_data['crseCode']} has set to {grade_letter}"
            )
            store[key] = grade_letter

            send_discord_webhook(
                webhook_url,
                message=f"Grade for **{grade_data['crseCode']}** has set to `{grade_letter}`",
            )

    save_store(store_path, store)

    logger.success("Letter grade check completed")
