import sys

from loguru import logger
from rich.console import Console

from canvas.announcements import check_canvas_announcements
from canvas.assignments import check_canvas_assignments
from canvas.grade_changes import check_grade_changes
from canvas.inbox import check_canvas_inbox
from discord.grab_useful_messages import get_useful_messages
from email_summarizer.app import email_summarize
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
            check_rss_news(),
            email_summarize(),
            check_canvas_inbox(),
            check_canvas_assignments(),
            check_canvas_announcements(),
            check_grade_changes(),
        ],
    ],
    ["Summarize Outlook emails", "email_summarize", email_summarize],
    [
        "Check Canvas assignments",
        "check_canvas_assignments",
        check_canvas_assignments,
    ],
    [
        "Check Canvas announcements",
        "check_canvas_announcements",
        check_canvas_announcements,
    ],
    [
        "Check Canvas inbox",
        "check_canvas_inbox",
        check_canvas_inbox,
    ],
    [
        "Check Canvas grades",
        "check_canvas_grades",
        check_grade_changes,
    ],
    [
        "Get useful Discord messages",
        "get_useful_discord_messages",
        get_useful_messages,
    ],
    [
        "Check RSS news",
        "check_rss_news",
        check_rss_news,
    ],
    [
        "Exit",
        "exit",
        lambda: sys.exit(0),
    ],
]

if len(sys.argv) > 1:
    short_code = sys.argv[1]

    # Find the function with the short code
    for function in function_list:
        if function[1] == short_code:
            function[2]()
            sys.exit(0)

    console.print("Invalid short code", style="red bold")
    console.print()

for i, function in enumerate(function_list):
    console.print(f"[{i + 1}] {function[0]}")

# Print empty line
console.print()

choice = input("Enter the number of the function you want to run: ")

console.print()

if (
    not choice.isdigit()
    or (int(choice) - 1) >= len(function_list)
    or (int(choice) - 1) < 0
):
    console.print(f"Invalid choice: {choice}", style="red bold")
    console.print()
    sys.exit(1)

function_list[int(choice) - 1][2]()
