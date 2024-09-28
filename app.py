import sys

from rich.console import Console

from email_summarizer.app import email_summarize
from usthing.book_library import book
from usthing.booking_availability import check_booking_status
from usthing.my_booking import get_booking

console = Console()
console.print(
    """
██╗   ██╗███████╗████████╗   ██████╗ ██╗   ██╗
██║   ██║██╔════╝╚══██╔══╝   ██╔══██╗╚██╗ ██╔╝
██║   ██║███████╗   ██║█████╗██████╔╝ ╚████╔╝ 
██║   ██║╚════██║   ██║╚════╝██╔═══╝   ╚██╔╝  
╚██████╔╝███████║   ██║      ██║        ██║   
 ╚═════╝ ╚══════╝   ╚═╝      ╚═╝        ╚═╝   
""",
    style="green",
)

function_list = [
    ["Email Summarizer", "email_summarize", email_summarize],
    ["Get Booking", "get_booking", get_booking],
    ["Get available library booking", "check_booking_status", check_booking_status],
    ["Book Library Room", "book_library", book],
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
