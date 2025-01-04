import sys

import undetected_chromedriver as uc
from loguru import logger
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")


def get_driver():
    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}
    return uc.Chrome(headless=False, desired_capabilities=caps)
