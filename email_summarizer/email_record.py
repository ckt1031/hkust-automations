import re
from datetime import datetime, timezone


def mark_email_as_checked(list: list[dict[str, str]], id: str):
    # Get current timestamp first
    iso_time = datetime.now(timezone.utc).astimezone().isoformat()

    # Add the id to the list, if it doesn't exist
    if not is_email_checked(list, id):
        list.append({id: iso_time})


def is_email_checked(list: list[dict[str, str]], id: str):
    # If id exists in the list as a key, return True
    for email in list:
        if email.get(id):
            return True

    return False


def check_email_sender(sender_email: str) -> bool:
    """
    Check if the email is from the expected sender
    """
    # regex which as ust or instruct
    reg = re.compile(r"ust|instruct|azure", re.IGNORECASE)

    if reg.search(sender_email):
        return True

    return False
