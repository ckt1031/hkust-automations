from loguru import logger

from discord.webhook import send_discord_webhook
from lib.env import getenv
from lib.onedrive_store import get_store, save_store
from usthing.api import get_class_enrollments


def check_course_wait_list():
    user_id = getenv("DISCORD_USER_ID")
    webhook_url = getenv("DISCORD_WEBHOOK_URL_CANVAS")

    if webhook_url is None:
        raise ValueError("DISCORD_WEBHOOK_URL_CANVAS is not set")

    if user_id is None:
        raise ValueError("DISCORD_USER_ID is not set")

    data = get_class_enrollments()
    waitlists = data["stdtInfo"][0]["studentClassWaitlist"]

    # "studentClassWaitlist": [
    # {
    #   "termCode": "2430",
    #   "crseId": "010699",
    #   "crseCode": "COMP2211",
    #   "classSections": [
    #     "L1",
    #     "LA1"
    #   ],
    #   "classes": [
    #     {
    #       "classNbr": 2073,
    #       "classSection": "L1"
    #     },
    #     {
    #       "classNbr": 2079,
    #       "classSection": "LA1"
    #     }
    #   ],
    #   "waitPosition": 14
    # },
    # {
    #   "termCode": "2430",
    #   "crseId": "000272",
    #   "crseCode": "IEDA2010",
    #   "classSections": [
    #     "L1",
    #     "T2"
    #   ],
    #   "classes": [
    #     {
    #       "classNbr": 2653,
    #       "classSection": "L1"
    #     },
    #     {
    #       "classNbr": 2657,
    #       "classSection": "T2"
    #     }
    #   ],
    #   "waitPosition": 5
    # },
    # {
    #   "termCode": "2430",
    #   "crseId": "001894",
    #   "crseCode": "MATH1014",
    #   "classSections": [
    #     "L10",
    #     "T10B"
    #   ],
    #   "classes": [
    #     {
    #       "classNbr": 3535,
    #       "classSection": "L10"
    #     },
    #     {
    #       "classNbr": 3571,
    #       "classSection": "T10B"
    #     }
    #   ],
    #   "waitPosition": 3
    # }

    store_path = "course_waitlist.json"
    store = get_store(store_path)

    # The structure of the store is:
    # {
    #     "course_code classSection": position_integer
    #     "COMP1021": 1
    #     "COMP2711": 2
    # }

    courses = []

    for waitlist in waitlists:
        key = waitlist["crseCode"]

        courses.append(key)

        # Situation 1: The course is not in the store but new course is added to the waitlist
        if store.get(key) is None:
            logger.info(f"{key} is added to the waitlist")

            store[key] = waitlist["waitPosition"]

            message = f"{key} added to the waitlist, current position: {waitlist['waitPosition']}"

            # embed = {
            #     "title": f"{key} added to the waitlist",
            #     "description": f"Current position in the waitlist: `{waitlist['waitPosition']}`",
            # }

        # Now compare the position in the store with the new position
        # Reminded that the position updated will not be larger than the previous one
        # Situation 2: The course is in the store and the course is still in the waitlist
        elif store[key] > waitlist["waitPosition"]:
            logger.info(f"{key} is updated in the waitlist")

            store[key] = waitlist["waitPosition"]

            message = f"{key} updated in the waitlist, current position: {waitlist['waitPosition']}"

        # If the course is in the store and the position is not updated, do nothing
        else:
            logger.info(f"{key} is in the waitlist, no update needed")
            continue

        # Add mention to the end of the message
        message += f" <@{user_id}>"

        # Send the embed to Discord
        send_discord_webhook(webhook_url, message=message)

    # Situation 3: The course is in the store but the course is removed from the waitlist
    store_keys = list(store.keys())
    for key in store_keys:
        if key not in courses:
            logger.info(f"{key} is removed from the waitlist")

            del store[key]

            message = f"{key} removed from the waitlist"

            # Add mention to the end of the message
            message += f" <@{user_id}>"

            # Send the embed to Discord
            send_discord_webhook(webhook_url, message=message)

    save_store(store_path, store)

    logger.success("Course waitlist checked")
