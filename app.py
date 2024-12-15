import sys

from loguru import logger
from rich.console import Console

from canvas.announcements import check_canvas_announcements
from canvas.assignments import check_canvas_assignments
from canvas.grade_changes import check_grade_changes
from canvas.inbox import check_canvas_inbox
from discord.grab_useful_messages import get_useful_messages
from outlook.summarize import email_summarize
from rss.news import check_rss_news

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")

console = Console()


function_list = [
    [
        "Run all below",
        "all",
        lambda: [
            try_run(check_rss_news),
            try_run(email_summarize),
            try_run(check_canvas_inbox),
            try_run(check_canvas_assignments),
            try_run(check_canvas_announcements),
            try_run(check_grade_changes),
        ],
    ],
    ["Summarize Outlook emails", "email_summarize", lambda: email_summarize()],
    [
        "Check Canvas assignments",
        "check_canvas_assignments",
        lambda: check_canvas_assignments(),
    ],
    [
        "Check Canvas announcements",
        "check_canvas_announcements",
        lambda: check_canvas_announcements(),
    ],
    [
        "Check Canvas inbox",
        "check_canvas_inbox",
        lambda: check_canvas_inbox(),
    ],
    [
        "Check Canvas grades",
        "check_canvas_grades",
        lambda: check_grade_changes(),
    ],
    [
        "Get useful Discord messages",
        "get_useful_discord_messages",
        lambda: get_useful_messages(),
    ],
    [
        "Check RSS news",
        "check_rss_news",
        lambda: check_rss_news(),
    ],
    [
        "Exit",
        "exit",
        lambda: sys.exit(0),
    ],
]


def try_run(action):
    try:
        action()
    except Exception as e:
        logger.error(f"Error running {action.__name__}: {e}")


if len(sys.argv) > 1:
    short_code = sys.argv[1]

    # Find the function with the short code
    for function in function_list:
        if function[1] == short_code:
            function[2]()
            sys.exit(0)

    console.print("Invalid short code\n", style="red bold")

for i, function in enumerate(function_list):
    console.print(f"[{i + 1}] {function[0]}")

# Print empty line
choice = input("\nEnter the number of the function you want to run: ")

if not choice.isdigit():
    console.print("\nChoice must be a number!", style="red bold")
    sys.exit(1)

choice_index = int(choice) - 1

if choice_index >= len(function_list) or choice_index < 0:
    console.print(f"\nInvalid choice: {choice}", style="red bold")
    sys.exit(1)

function_list[choice_index][2]()
