import hashlib
import shelve


def open_db():
    return shelve.open("data")


def hash_string_sha256(input_string):
    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the bytes of the input string
    sha256_hash.update(input_string.encode("utf-8"))

    # Get the hexadecimal representation of the hash
    return sha256_hash.hexdigest()


def is_email_checked(email_subject):
    # Hash the email subject
    key = hash_string_sha256(email_subject)

    with open_db() as db:
        return key in db


def mark_email_as_checked(email_subject):
    key = hash_string_sha256(email_subject)
    with open_db() as db:
        db[key] = True
