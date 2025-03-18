import sys

from loguru import logger

from lib.canvas.announcements import check_canvas_announcements
from lib.canvas.assignment_submission import check_canvas_assignments_submissions
from lib.canvas.assignments import check_canvas_assignments
from lib.canvas.grade_changes import check_canvas_grade_changes
from lib.canvas.inbox import check_canvas_inbox
from lib.outlook.summarize import email_summarize
from lib.usthing.course_wait_list import check_course_wait_list
from lib.usthing.letter_grade_change import check_letter_grade_change

# Remove loggers time, level
logger.remove()
logger.add(sys.stdout, format="{time}: [<level>{level}</level>] {message}")

function_dict = {
    "all": lambda: print("Running all tasks..."),
    "email_summarize": email_summarize,
    "check_canvas_assignments": check_canvas_assignments,
    "check_canvas_announcements": check_canvas_announcements,
    "check_canvas_inbox": check_canvas_inbox,
    "check_canvas_grades": check_canvas_grade_changes,
    "check_canvas_assignments_submissions": check_canvas_assignments_submissions,
    "check_letter_grade_change": check_letter_grade_change,
    "check_course_wait_list": check_course_wait_list,
    "exit": lambda: sys.exit(0),
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        short_code = sys.argv[1]

        # If the short_code is all, run all tasks, but prevent the user from running the exit task
        if short_code == "all":
            for name, func in function_dict.items():
                if name != "exit":
                    func()

            # Exit after running all tasks
            sys.exit(0)

        if short_code in function_dict:
            function_dict[short_code]()
        else:
            raise ValueError("Invalid short code")

        sys.exit(0)

    for i, (name, func) in enumerate(function_dict.items(), 1):
        print(f"[{i}] {name.replace('_', ' ').title()}")

    choice = input("\nEnter the number of the task you want to run: ")

    if not choice.isdigit():
        raise ValueError(f"Invalid task: {choice}")

    choice_index = int(choice) - 1

    if choice_index >= len(function_dict) or choice_index < 0:
        raise ValueError(f"Invalid task: {choice}")

    list(function_dict.values())[choice_index]()
