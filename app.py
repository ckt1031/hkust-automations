import sys

from loguru import logger

from canvas.announcements import check_canvas_announcements
from canvas.assignment_quizzes_table import print_assignments_quizzes_table
from canvas.assignment_submission import check_canvas_assignments_submissions
from canvas.assignments import check_canvas_assignments
from canvas.discussions import check_discussions
from canvas.download_canvas_content import download_canvas_content
from canvas.grade_changes import check_grade_changes
from canvas.inbox import check_canvas_inbox
from discord.grab_useful_messages import check_discord_servers
from outlook.summarize import email_summarize
from reddit.check import check_reddit
from usthing.course_wait_list import check_course_wait_list
from usthing.letter_grade_change import check_letter_grade_change

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")

function_dict = {
    "all": lambda: [
        email_summarize(),
        check_canvas_inbox(),
        check_canvas_assignments(),
        check_canvas_announcements(),
        check_grade_changes(),
    ],
    "email_summarize": email_summarize,
    "check_canvas_assignments": check_canvas_assignments,
    "check_canvas_announcements": check_canvas_announcements,
    "check_canvas_inbox": check_canvas_inbox,
    "check_canvas_grades": check_grade_changes,
    "check_canvas_assignments_submissions": check_canvas_assignments_submissions,
    "check_canvas_discussions": check_discussions,
    "check_discord_servers": check_discord_servers,
    "check_letter_grade_change": check_letter_grade_change,
    "check_reddit": check_reddit,
    "download_canvas_content": download_canvas_content,
    "print_assignments_quizzes_table": print_assignments_quizzes_table,
    "check_course_wait_list": check_course_wait_list,
    "exit": lambda: sys.exit(0),
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        short_code = sys.argv[1]
        if short_code in function_dict:
            function_dict[short_code]()
        else:
            raise ValueError("Invalid short code")
        sys.exit(0)

    for i, (name, func) in enumerate(function_dict.items(), 1):
        print(f"[{i}] {name.replace('_', ' ').title()}")

    choice = input("\nEnter the number of the function you want to run: ")

    if not choice.isdigit():
        raise ValueError(f"Invalid choice: {choice}")

    choice_index = int(choice) - 1

    if choice_index >= len(function_dict) or choice_index < 0:
        raise ValueError(f"Invalid choice: {choice}")

    list(function_dict.values())[choice_index]()
