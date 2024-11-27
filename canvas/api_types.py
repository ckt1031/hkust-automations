from datetime import datetime

import msgspec


class CourseListItem(msgspec.Struct):
    id: int
    name: str
    course_code: str


class AssignmentListItem(msgspec.Struct):
    id: int
    name: str
    html_url: str
    graded_submissions_exist: bool
    has_submitted_submissions: bool

    due_at: datetime | None = None
    course_name: str | None = None


class DiscussionTopicListItemAuthor(msgspec.Struct):
    avatar_image_url: str | None = None


class DiscussionTopicListItem(msgspec.Struct):
    id: int
    title: str
    posted_at: datetime
    message: str
    html_url: str
    author: DiscussionTopicListItemAuthor
    user_name: str | None = None


class DiscussionTopicItemView(msgspec.Struct):
    id: int


class ConversationsListItem(msgspec.Struct):
    id: int
    subject: str
    last_message_at: datetime
    context_name: str
    avatar_url: str
    participants: list[dict]
    messages: list[dict]
