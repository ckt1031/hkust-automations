import hashlib
import math
import re
from datetime import datetime, timezone

from dateutil import parser


def sha2_256(text: str) -> str:
    return hashlib.sha3_256(text.encode()).hexdigest()


def get_ms(date: str):
    parsed_date = parser.parse(date)

    # Ensure parsed_date is timezone-aware
    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)

    return parsed_date.timestamp()


def remove_massive_space(text):
    return re.sub(r"\s+", " ", text)


def clean_html(raw_html: str) -> str:
    """
    Clean HTML tags from the raw HTML content
    """

    clean = re.compile("<.*?>")  # Regular expression to match HTML tags
    return re.sub(clean, "", raw_html)  # Return text without HTML tags


# Function to remove CSS and scripts from HTML
def remove_css_and_scripts(raw_html: str) -> str:
    """
    Remove CSS and scripts from the HTML content
    """
    # Remove style tags
    raw_html = re.sub(r"<style.*?>.*?</style>", "", raw_html, flags=re.DOTALL)
    # Remove script tags
    raw_html = re.sub(r"<script.*?>.*?</script>", "", raw_html, flags=re.DOTALL)
    return raw_html


def get_current_iso_time():
    return datetime.now(timezone.utc).astimezone().isoformat()


def iso_time_from_now_second_left(t: str):
    """
    Return the difference in seconds between the current time and the given time
    """
    float_diff = (
        datetime.fromisoformat(t).timestamp() - datetime.now(timezone.utc).timestamp()
    )

    return math.ceil(float_diff)
