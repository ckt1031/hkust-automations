"""
This script retrieves unexpected emails from the email list based on previous run results.
This applies to both GitHub Actions runs and local script executions.
"""

import os
import sys

from loguru import logger

from db import get_all_unexpected_sender

UNEXPECTED_SENDER_TXT_PATH = "unexpected_sender.txt"


def save_sender_to_text(sender: str) -> None:
    # If os exists, write the sender to the file
    if os.path.exists(UNEXPECTED_SENDER_TXT_PATH):
        # Check if the sender is already in the file
        with open(UNEXPECTED_SENDER_TXT_PATH, "r") as f:
            lines = f.readlines()
            for line in lines:
                if sender in line:
                    return

        with open(UNEXPECTED_SENDER_TXT_PATH, "a") as f:
            # In new line
            f.write("\n" + sender)
    else:
        with open(UNEXPECTED_SENDER_TXT_PATH, "w") as f:
            f.write(sender)


if __name__ == "__main__":
    senders = get_all_unexpected_sender()

    if len(senders) == 0:
        logger.success("No unexpected sender found")
        sys.exit(0)

    index = 0

    for email in senders:

        email = email.decode("utf-8")

        if len(senders) < 20:
            index += 1
            logger.success(f"{index}. {email}")

        save_sender_to_text(email)
