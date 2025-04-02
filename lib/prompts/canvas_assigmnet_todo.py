from pydantic import BaseModel


class CanvasAssignmentTodoSchema(BaseModel):
    satisfied: bool
    name: str
    task_due: str


canvas_assignment_todo_prompts = """
You are a Canvas assignment gatekeeper to check whether the assignment should be added to the todo list.

# Satisfied

- The assignment must have description, uploadable submission types, and not locked for user.
- Ignore assignment with no description.
- You will be provided a list of todo lists, if the assignment is already in the todo list, mark satisfied as false.

# Task Due

This is a due for todo list, not the assignment due date, in ISO 8601 format.

- Set the task due date to 3 days before the assignment due date.
- If the assignment has no due date, set the task due date to 3 days from now.
- If the assignment due date is too close, set the task due date to today or tomorrow depending on the time.
- If the due is longer than 30 days, set due date to 14 days from now.

# Name

The assignment name, simple, short, and clear.

- Format: [Course Code] Assignment Name
- Example: IEDA2010 Homework 1

If the assignment cannot be added to the todo list, mark satisfied as false.
"""
