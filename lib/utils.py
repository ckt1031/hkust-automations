import re
import urllib.parse

from html2text import HTML2Text
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from lib.api.discord import send_discord_webhook


def wrap_all_markdown_link(text: str) -> str:
    """
    Wrap the text with markdown link format.

    Args:
        text (str): The text to wrap.

    Returns:
        str: The wrapped text.
    """
    import re

    return re.sub(
        r"(\[.*?\]\()(.*?)(\))",
        lambda m: f"{m.group(1)}<{m.group(2)}>{m.group(3)}",
        text,
    )


def split_text_and_send_to_discord(text: str, webhook_url: str):
    headers_to_split_on = [
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        strip_headers=False,
        headers_to_split_on=headers_to_split_on,
    )
    result = markdown_splitter.split_text(text)

    chunk_size = 1900
    chunk_overlap = 100
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    result = text_splitter.split_documents(result)

    for split in result:
        send_discord_webhook(webhook_url, message=split.page_content, username="Email")


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
