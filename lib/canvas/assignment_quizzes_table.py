from canvas.assignment_submission import get_assignment_submissions
from loguru import logger
from prettytable import PrettyTable


def print_assignments_quizzes_table():
    logger.info("Printing assignments and quizzes table")

    assignments = get_assignment_submissions()

    table = PrettyTable()
    # Align columns to the left
    table.align = "l"
    table.field_names = [
        "Name",
        "Course",
        "Due Date",
    ]

    for assignment in assignments:
        table.add_row(
            [
                assignment["name"],
                assignment["course_code"],
                assignment["due_at"],
            ]
        )

    print(table)
