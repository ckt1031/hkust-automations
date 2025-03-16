import re


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
