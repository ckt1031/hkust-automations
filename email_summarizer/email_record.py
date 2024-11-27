import re
from datetime import datetime, timedelta, timezone

from loguru import logger

from lib.onedrive_store import is_recorded
from lib.utils import get_current_iso_time


def prune_email_record(list: list[dict[str, datetime]]) -> list[dict[str, datetime]]:
    """
    Prune the email record to remove emails older than 7
    days
    """

    for email in list:
        for _, value in email.items():
            # If the email is older than 7 days, remove it
            if value < (datetime.now(timezone.utc) - timedelta(days=7)):
                # Remove the email from the list
                list.remove(email)

                logger.debug(f"Email {email} removed from the record")

    return list


def mark_email_as_checked(list: list[dict[str, datetime]], id: str):
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

    return reg.search(sender_email) is not None
