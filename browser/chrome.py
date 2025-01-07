def get_driver():
    import undetected_chromedriver as uc
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}
    return uc.Chrome(headless=False, desired_capabilities=caps, use_subprocess=True)
