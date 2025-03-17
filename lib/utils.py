import re
import urllib.parse

import html2text
from loguru import logger


def remove_excessive_new_lines(text: str) -> str:
    return "\n".join([line for line in text.split("\n") if line.strip()])


def convert_safelinks_from_text(text: str) -> str:
    """
    Converts Safe Links URLs found within a plain text string to their original URLs.

    Args:
        text: The input text string potentially containing Safe Links URLs.

    Returns:
        The text string with Safe Links URLs replaced by their original URLs.
        If a Safe Link cannot be decoded, it is left unchanged.
    """

    def decode_safe_link(safe_link_url):
        """Decodes a single Safe Links URL."""
        try:
            parsed_url = urllib.parse.urlparse(safe_link_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            original_url = query_params.get("url", [None])[0]  # Get the 'url' parameter
            return original_url
        except Exception as e:
            logger.debug(f"Error decoding URL: {safe_link_url} - {e}")

            return safe_link_url  # Return the original if decoding fails

    # Regular expression to match Safe Links URLs.  This is improved for robustness.
    safe_link_pattern = r"(https?://[^\s]*safelinks\.protection\.outlook\.com[^\s]*)"

    def replace_safe_link(match):
        """
        Callback function for re.sub.  Decodes the matched Safe Link and returns
        the original URL or the Safe Link if decoding fails.
        """
        safe_link = match.group(1)
        decoded_url = decode_safe_link(safe_link)
        return decoded_url if decoded_url else safe_link

    # Use re.sub to find all Safe Links and replace them with the decoded URLs.
    return re.sub(safe_link_pattern, replace_safe_link, text)


def process_html_to_text(html: str) -> str:
    txt = html2text.HTML2Text(bodywidth=0)
    txt.ignore_emphasis = True
    txt.ignore_images = True

    final_text = txt.handle(html)
    final_text = remove_excessive_new_lines(final_text)
    final_text = convert_safelinks_from_text(final_text)

    return final_text
