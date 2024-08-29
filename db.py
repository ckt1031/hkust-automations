import hashlib
import shelve
from datetime import timezone

from dateutil import parser


def open_db():
    return shelve.open("data")


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
    with open_db() as db:
        return key in db


def save_record(key: str, value: bool):
    with open_db() as db:
        db[key] = value


def is_email_checked(email_subject: str, date: str):
    # Hash the email subject
    key = hash_string_sha256(f"{email_subject} - {get_ms(date)}")

    return is_record_exist(key)


def mark_email_as_checked(email_subject: str, date: str):
    key = hash_string_sha256(f"{email_subject} - {get_ms(date)}")
    save_record(key, True)
