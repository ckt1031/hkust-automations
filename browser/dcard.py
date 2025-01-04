import json
from time import sleep

import html2text
from loguru import logger
from selenium.webdriver.common.keys import Keys
from undetected_chromedriver import Chrome

from browser.chrome import get_driver
from lib.openai_api import generate_schema
from prompts.dcard import UsefulDcardPostSelection, useful_dcard_post_selection_prompts

DCARD_FORUM = "hkust"
DCARD_BASE_URL = f"https://www.dcard.tw/f/{DCARD_FORUM}"


def process_entry(entry):
    return json.loads(entry["message"])["message"]


def get_network_logs(driver: Chrome, url_filler: str):
    # Get network log entries
    logs = driver.get_log("performance")
    logs = [json.loads(entry["message"])["message"] for entry in logs]

    # Filter the log entries, starting with {dcard_paging_url}
    logs = [
        entry for entry in logs
        if entry["method"] == "Network.requestWillBeSent" and url_filler in entry["params"]["request"]["url"]
    ]

    results = []

    for log in logs:
        requestId = log["params"]["requestId"]

        # Get the response body
        data = driver.execute_cdp_cmd(
            "Network.getResponseBody", {"requestId": requestId}
        )

        body = json.loads(data["body"])

        results.append({
            "requestId": requestId,
            "body": body
        })

    return results


def scrape_dcard():
    driver = get_driver()
    driver.get(DCARD_BASE_URL)

    # Wait for the page to load
    driver.implicitly_wait(5)

    # Get the title of the page
    logger.success(f"Obtained Title: {driver.title}")

    buttons = ["最新", "熱門"]

    for button in buttons:
        # Click the button
        driver.find_element("xpath", f'//a[text()="{button}"]').click()

        logger.success(f"Clicked the {button} button to switch tabs")

        for i in range(15):
            # Scroll to the bottom
            driver.find_element("css selector", "body").send_keys(Keys.END)

            logger.debug(f"Scrolled to the bottom ({i + 1})")

            # Wait for the page to load
            sleep(0.2)

        sleep(5)

        dcard_paging_url = "https://www.dcard.tw/service/api/v2/globalPaging/page"
        paging_logs = get_network_logs(driver, dcard_paging_url)

        all_posts_text = ""
        posts_list = []

        for log in paging_logs:
            body = log["body"]
            if "widgets" not in body:
                logger.error(f"Request ID: {log['requestId']} does not contain any widgets")
                continue

            # Process the entry
            for widget in body["widgets"]:
                items = widget["forumList"]["items"]

                for item in items:
                    post = item["post"]

                    posts_list.append(
                        {
                            "id": post["id"],
                            "likeCount": post["likeCount"],
                            "commentCount": post["commentCount"],
                            "title": post["title"],
                            "excerpt": post["excerpt"],
                        }
                    )

                    all_posts_text += f"ID: {post['id']}\nTitle: {post['title']}\nExcept: {post['excerpt']}\nComments: {post['commentCount']}\nLikes: {post['likeCount']}\n\n"

        if len(posts_list) == 0:
            logger.error("No posts were obtained")
            continue

        logger.success(f"Obtained {len(posts_list)} posts from Dcard")

        selection_res = generate_schema(
            useful_dcard_post_selection_prompts,
            all_posts_text.strip(),
            UsefulDcardPostSelection,
        )

        if not selection_res or len(selection_res.post_ids) == 0:
            logger.info("No posts were selected")
            continue

        selected_posts = [
            post for post in posts_list if post["id"] in selection_res.post_ids
        ]

        logger.success(f"Selected {len(selected_posts)} posts")

        h = html2text.HTML2Text()
        h.ignore_links = True

        post_list = []

        for post in selected_posts:
            post_list_item = {}

            post_url = f"{DCARD_BASE_URL}/p/{post['id']}"

            driver.get(post_url)

            # Wait for the page to load
            driver.implicitly_wait(3)

            # Obtain <article> element
            article = driver.find_element("css selector", "article")

            # Only obtain <span> elements
            article = article.find_elements("tag name", "span")

            for n in article:
                # Obtain the page source
                page_source = n.get_attribute("outerHTML")

                post_list_item = {
                    "id": post['id'],
                    "title": post['title'],
                    "content": h.handle(page_source).strip(),
                    "comments": []
                }

            # Scroll to the bottom
            driver.find_element("css selector", "body").send_keys(Keys.END)

            sleep(1)

            dcard_comments_url = f"https://www.dcard.tw/service/api/v2/posts/{post['id']}/comments"

            # Get the comments
            logs = get_network_logs(driver, dcard_comments_url)

            for log in logs:
                comments = log["body"]

                for comment in comments:
                    if "content" not in comment:
                        logger.error(f"Comment does not contain content (Req ID: {log['requestId']})")
                        continue

                    post_list_item["comments"].append(
                        {
                            "content": comment["content"],
                            "likeCount": comment["likeCount"],
                        }
                    )

            sleep(3)

            print(post_list_item)

            post_list.append(post_list_item)

        logger.success(f"Obtained {len(post_list)} posts with comments")

        # Back to the main page
        driver.get(DCARD_BASE_URL)
        # Click the button
        driver.find_element("xpath", f'//a[text()="{button}"]').click()

    driver.quit()


if __name__ == "__main__":
    scrape_dcard()
