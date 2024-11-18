import sys

from loguru import logger
from rich.console import Console

from canvas.assignments import check_assignments
from canvas.inbox import check_inbox
from email_summarizer.app import email_summarize

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")

console = Console()

function_list = [
    [
        "Run all below",
        "all",
        lambda: [check_assignments(), check_inbox(), email_summarize()],
    ],
    ["Summarize Outlook emails", "email_summarize", email_summarize],
    [
        "Check Canvas assignments",
        "check_canvas_assignments",
        check_assignments,
    ],
    [
        "Check Canvas inbox",
        "check_canvas_inbox",
        check_inbox,
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
    console.print(f"[{i}] {function[0]}")

# Print empty line
console.print()

choice = int(input("Enter the number of the function you want to run: "))
console.print()
function_list[choice][2]()
