import re
from datetime import datetime, timedelta, timezone

from loguru import logger


def prune_email_store(data: dict[str, datetime]):
    """
    Prune the email store to remove emails older than 7
    days
    """

    new_list = data.copy()

    for item_id, value in data.items():
        # If the email is older than 7 days, remove it
        if value < (datetime.now(timezone.utc) - timedelta(days=7)):
            # Remove the email from the list
            del new_list[item_id]

            logger.debug(f"Email {item_id} removed from the store (older than 7 days)")

    return new_list


def check_email_sender(sender_email: str) -> bool:
    """
    Check if the email is from the expected sender,
    which is either "ust", "instruct" or "azure"
    """
    # regex which as ust or instruct
    reg = re.compile(r"ust|instruct|azure", re.IGNORECASE)

    return reg.search(sender_email) is not None
