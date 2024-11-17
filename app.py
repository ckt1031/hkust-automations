import sys

from rich.console import Console

from canvas.assignments import check_assignments
from canvas.inbox import check_inbox
from email_summarizer.app import email_summarize

console = Console()

function_list = [
    ["Email Summarizer", "email_summarize", email_summarize],
    [
        "Check Canvas Assignments",
        "check_canvas_assignments",
        check_assignments,
    ],
    [
        "Check Canvas inbox",
        "check_canvas_inbox",
        check_inbox,
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
