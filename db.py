import hashlib
import os
import sys
from datetime import timezone

import dotenv
import redis
from dateutil import parser

dotenv.load_dotenv()

redis_client = None

if not redis_client:
    try:
        redis_connection_string = os.environ["REDIS_CONNECTION_STRING"]

        redis_client = redis.from_url(redis_connection_string)
    except KeyError:
        sys.exit("REDIS_CONNECTION_STRING environment variable is not set")


def hash_string_sha256(input_string: str):
    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the bytes of the input string
    sha256_hash.update(input_string.encode("utf-8"))

    # Get the hexadecimal representation of the hash
    return sha256_hash.hexdigest()


def get_ms(date: str):
    parsed_date = parser.parse(date)

    # Ensure parsed_date is timezone-aware
    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)

    return parsed_date.timestamp()


def is_record_exist(key: str):
    return redis_client.exists(key)


def save_unexpected_email_sender(sender: str):
    # Save the sender in list or create it if it doesn't exist
    redis_client.sadd("unexpected_email_senders", sender)


def get_all_unexpected_sender():
    return redis_client.smembers("unexpected_email_senders")


def save_email_record(key: str, value: bool, expire_time: int = -1):
    # 0 for False, 1 for True
    redis_client.set(key, int(value), ex=None if expire_time == -1 else expire_time)


def is_email_checked(email_subject: str, date: str):
    # Hash the email subject
    key = hash_string_sha256(f"{email_subject} - {get_ms(date)}")

    return is_record_exist(key)


def mark_email_as_checked(email_subject: str, date: str):
    key = hash_string_sha256(f"{email_subject} - {get_ms(date)}")
    expiring_time_in_seconds = 60 * 60 * 24 * 3  # 3 days
    save_email_record(key, True, expiring_time_in_seconds)
