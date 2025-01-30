def get_driver():
    from seleniumbase import Driver

    return Driver(uc=True, headless=False, uc_subprocess=True, undetectable=True)
