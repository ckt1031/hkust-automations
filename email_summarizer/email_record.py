import re

import lib.redis as redis
from lib.hashing import hash_string_sha256


def mark_email_as_checked(_id: str):
    key = hash_string_sha256(f"MS_EMAIL_CHECKED_{_id}")

    expiring_time_in_seconds = 60 * 60 * 24 * 14  # 14 days

    redis.set_redis_boolean_value(key, True, expiring_time_in_seconds)


def is_email_checked(_id: str):
    # Hash the email subject
    key = hash_string_sha256(f"MS_EMAIL_CHECKED_{_id}")

    return redis.is_record_exist(key)


def check_email_sender(sender_email: str) -> bool:
    """
    Check if the email is from the expected sender
    """
    # regex which as ust or instruct
    reg = re.compile(r"ust|instruct|azure", re.IGNORECASE)

    if reg.search(sender_email):
        return True

    return False
