import re
from datetime import datetime, timezone


def prune_email_record(list: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Prune the email record to remove emails older than 7
    days
    """
    # Get current timestamp first
    iso_time = datetime.now(timezone.utc).astimezone()

    for email in list:
        for key, value in email.items():
            # Get the email timestamp
            email_time = datetime.fromisoformat(value)

            # If the email is older than 7 days, remove it
            if (iso_time - email_time).days > 7:
                list.remove(email)

    return list


def mark_email_as_checked(list: list[dict[str, str]], id: str):
    """
    Mark the email as checked by adding it to the list
    with the current timestamp
    """
    # Get current timestamp first
    iso_time = datetime.now(timezone.utc).astimezone().isoformat()

    # Add the id to the list, if it doesn't exist
    if not is_email_checked(list, id):
        list.append({id: iso_time})

    return list


def is_email_checked(list: list[dict[str, str]], id: str):
    # If id exists in the list as a key, return True
    for email in list:
        if email.get(id):
            return True

    return False


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
