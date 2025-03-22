import sys

from loguru import logger

from lib.canvas import (
    notify_canvas_new_announcements,
    notify_canvas_new_assignments,
    notify_canvas_new_canvas_assignments_submissions,
    notify_canvas_new_canvas_grades,
    notify_canvas_new_canvas_inbox,
)
from lib.outlook.summarize import summarize_outlook
from lib.usthing.course_wait_list import notify_course_wait_list
from lib.usthing.letter_grade_change import notify_letter_grade_change

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")


def run_all():
    print("Running all tasks...")

    for name, func in function_dict.items():
        if name != "exit" and name != "all":
            func()

    sys.exit(0)  # Exit after running all tasks


function_dict = {
    "all": run_all,
    "summarize_outlook": summarize_outlook,
    "notify_canvas_new_assignments": notify_canvas_new_assignments,
    "notify_canvas_new_announcements": notify_canvas_new_announcements,
    "notify_canvas_new_canvas_inbox": notify_canvas_new_canvas_inbox,
    "notify_canvas_new_canvas_grades": notify_canvas_new_canvas_grades,
    "notify_canvas_new_canvas_assignments_submissions": notify_canvas_new_canvas_assignments_submissions,
    "notify_letter_grade_change": notify_letter_grade_change,
    "notify_course_wait_list": notify_course_wait_list,
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

    choice = input("\nEnter the number of the task you want to run: ")

    # Print new line
    print()

    if not choice.isdigit():
        raise ValueError(f"Invalid task: {choice}")

    choice_index = int(choice) - 1

    if choice_index >= len(function_dict) or choice_index < 0:
        raise ValueError(f"Invalid task: {choice}")

    list(function_dict.values())[choice_index]()
