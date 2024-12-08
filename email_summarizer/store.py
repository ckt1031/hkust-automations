import re
from datetime import datetime, timedelta, timezone

from loguru import logger


def prune_email_store(list: dict[str, datetime]):
    """
    Prune the email store to remove emails older than 7
    days
    """

    for id, value in list.items():
        # If the email is older than 7 days, remove it
        if value < (datetime.now(timezone.utc) - timedelta(days=7)):
            # Remove the email from the list
            del list[id]

            logger.debug(f"Email {id} removed from the store (older than 7 days)")

    return list


def check_email_sender(sender_email: str) -> bool:
    """
    Check if the email is from the expected sender,
    which is either "ust", "instruct" or "azure"
    """
    # regex which as ust or instruct
    reg = re.compile(r"ust|instruct|azure", re.IGNORECASE)

    return reg.search(sender_email) is not None
