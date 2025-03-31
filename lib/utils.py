import re
import sys
import urllib.parse

from html2text import HTML2Text
from loguru import logger


def remove_excessive_new_lines(text: str) -> str:
    return "\n".join([line for line in text.split("\n") if line.strip()])


def replace_safe_link(match: re.Match) -> str:
    """
    Callback function for re.sub.  Decodes the matched Safe Link and returns
    the original URL or the Safe Link if decoding fails.
    """
    # Check if the match is valid and has a group.
    if match is None or match.lastindex is None:
        return match.group(0)

    safe_link = match.group(1)

    # Decode the Safe Link URL.
    try:
        return urllib.parse.unquote(safe_link)
    except Exception as e:
        logger.warning(f"Failed to decode Safe Link: {safe_link}", e)

        # Return the original Safe Link if decoding fails.
        return safe_link


def convert_safelinks_from_text(text: str) -> str:
    """
    Converts Safe Links URLs found within a plain text string to their original URLs.

    Args:
        text: The input text string potentially containing Safe Links URLs.

    Returns:
        The text string with Safe Links URLs replaced by their original URLs.
        If a Safe Link cannot be decoded, it is left unchanged.
    """

    # Regular expression to match Safe Links URLs.  This is improved for robustness.
    safe_link_pattern = (
        r"https?:\/\/.*safelinks\.protection\.outlook\.com\/\\?.*[?&]url=([^&]*)&"
    )

    # Use re.sub to find all Safe Links and replace them with the decoded URLs.
    return re.sub(safe_link_pattern, replace_safe_link, text)


def process_html_to_text(html: str) -> str:
    txt = HTML2Text(bodywidth=0)
    txt.ignore_emphasis = True
    txt.ignore_images = True

    final_text = txt.handle(html)
    final_text = remove_excessive_new_lines(final_text)
    final_text = convert_safelinks_from_text(final_text)

    return final_text


def check_if_arg_exists(arg: str) -> bool:
    """
    Check if the argument exists in the command line arguments.
    """
    return arg in sys.argv
