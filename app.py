import sys

from loguru import logger

from canvas.announcements import check_canvas_announcements
from canvas.assignments import check_canvas_assignments
from canvas.grade_changes import check_grade_changes
from canvas.inbox import check_canvas_inbox
from discord.grab_useful_messages import get_useful_messages
from outlook.summarize import email_summarize
from rss.news import check_rss_news
from usthing.letter_grade_change import check_letter_grade_change

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")


def try_run(action):
    def wrapper():
        try:
            action()
        except Exception as e:
            logger.error(f"Error running {action.__name__}: {e}")

    return wrapper


function_dict = {
    "all": try_run(
        lambda: [
            email_summarize(),
            check_canvas_inbox(),
            check_canvas_assignments(),
            check_canvas_announcements(),
            check_grade_changes(),
            check_letter_grade_change(),
        ]
    ),
    "email_summarize": try_run(email_summarize),
    "check_canvas_assignments": try_run(check_canvas_assignments),
    "check_canvas_announcements": try_run(check_canvas_announcements),
    "check_canvas_inbox": try_run(check_canvas_inbox),
    "check_canvas_grades": try_run(check_grade_changes),
    "get_useful_discord_messages": try_run(get_useful_messages),
    "check_rss_news": try_run(check_rss_news),
    "check_letter_grade_change": try_run(check_letter_grade_change),
    "exit": lambda: sys.exit(0),
}

if len(sys.argv) > 1:
    short_code = sys.argv[1]
    if short_code in function_dict:
        function_dict[short_code]()
    else:
        print("Invalid short code\n")
    sys.exit(0)

for i, (name, func) in enumerate(function_dict.items(), 1):
    print(f"[{i}] {name.replace('_', ' ').title()}")

choice = input("\nEnter the number of the function you want to run: ")

if not choice.isdigit():
    print("\nChoice must be a number!")
    sys.exit(1)

choice_index = int(choice) - 1

if choice_index >= len(function_dict) or choice_index < 0:
    print(f"\nInvalid choice: {choice}")
    sys.exit(1)

list(function_dict.values())[choice_index]()
