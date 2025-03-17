from datetime import datetime, timedelta, timezone

from loguru import logger


def prune_email_store(data: dict[str, datetime]) -> dict[str, datetime]:
    """
    Prunes the email store to remove emails older than 7 days.
    Creates a new dictionary containing only emails within the last 7 days.

    Args:
        data: A dictionary where keys are email IDs (str) and values are
            datetimes (datetime) representing the email's timestamp.

    Returns:
        A new dictionary containing only the emails that are not older than 7 days.
    """
    new_dict = {}
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

    for item_id, value in data.items():
        if value >= cutoff_date:  # Keep emails that are *not* older than 7 days
            new_dict[item_id] = value
        else:
            logger.debug(f"Email {item_id} removed from the store (older than 7 days)")

    return new_dict
