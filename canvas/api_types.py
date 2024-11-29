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


class AssignmeGroupAssigmentItemSubmission(msgspec.Struct):
    id: int
    grade: str | None = None
    submitted_at: datetime | None = None


class AssignmeGroupAssigmentItem(msgspec.Struct):
    id: int
    name: str
    html_url: str

    description: str | None = None
    points_possible: float | None = None
    submission: AssignmeGroupAssigmentItemSubmission | None = None


class AssignmeGroupItem(msgspec.Struct):
    id: int
    name: str
    assignments: list[AssignmeGroupAssigmentItem] | None = None


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


class ConversationsListItemParticipant(msgspec.Struct):
    name: str
    avatar_image_url: str | None = None


class ConversationsListItemMessage(msgspec.Struct):
    body: str


class ConversationsListItem(msgspec.Struct):
    id: int
    last_message_at: datetime
    avatar_url: str
    participants: list[ConversationsListItemParticipant]
    subject: str | None = None
    context_name: str | None = None


class ConversationsDetail(msgspec.Struct):
    messages: list[ConversationsListItemMessage]
