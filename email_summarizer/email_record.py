import re

from loguru import logger

from lib.onedrive_store import is_recorded
from lib.utils import get_current_iso_time, iso_time_from_now_second_left


def prune_email_record(list: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Prune the email record to remove emails older than 7
    days
    """

    for email in list:
        for _, value in email.items():
            # If the email is older than 7 days, remove it
            if iso_time_from_now_second_left(value) < -7 * 24 * 60 * 60:
                list.remove(email)

                logger.info(f"Email {email} removed from the record")

    return list


def mark_email_as_checked(list: list[dict[str, str]], id: str):
    """
    Mark the email as checked by adding it to the list
    with the current timestamp
    """
    # Get current timestamp first
    iso_time = get_current_iso_time()

    # Add the id to the list, if it doesn't exist
    if not is_recorded(list, id):
        list.append({id: iso_time})

    return list


def check_email_sender(sender_email: str) -> bool:
    """
    Check if the email is from the expected sender,
    which is either "ust", "instruct" or "azure"
    """
    # regex which as ust or instruct
    reg = re.compile(r"ust|instruct|azure", re.IGNORECASE)

    if reg.search(sender_email):
        return True

    return False
