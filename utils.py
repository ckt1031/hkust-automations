import email
import re
from datetime import datetime


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


def check_email_sender(sender: str) -> bool:
    """
    Check if the email is from the expected sender
    """

    # Google emails like account recovery, security alerts, etc., are not needed
    if sender.startswith("Google"):
        return False

    sender_email = get_sender_email(sender)

    if sender_email.endswith("google.com"):
        return False

    # If email includes ust.hk, then it's from the university
    if "ust.hk" in sender_email:
        return True

    return False


def get_sender_email(msg_from: str) -> str:
    """
    Get the sender's
    """
    email = re.findall(r"<(.+)>", msg_from)
    return email[0] if email else msg_from


def check_email_date(date: str, hours: int) -> bool:
    """
    Check if the email is newer than the specified hours
    """
    # Parse the email date: Tue, 27 Aug 2024 06:22:46 GMT
    email_date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
    # Get the current time
    current_time = datetime.now()
    # Calculate the difference in hours
    time_diff = current_time - email_date

    return time_diff.total_seconds() / 3600 < hours
