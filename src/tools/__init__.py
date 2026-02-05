"""Tools package for the chatbot."""
from .email_tool import send_email, read_emails, search_emails
from .calendar_tool import (
    schedule_meeting,
    list_upcoming_events,
    check_conflicts,
    find_available_slots,
    cancel_meeting,
    update_meeting,
    get_event_details,
    add_attendees_to_event
)
from .task_tool import (
    create_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task,
    get_upcoming_deadlines
)
from .knowledge_tool import search_knowledge_base
from .web_search_tool import web_search, search_news

__all__ = [
    "send_email",
    "read_emails",
    "search_emails",
    "schedule_meeting",
    "list_upcoming_events",
    "check_conflicts",
    "find_available_slots",
    "cancel_meeting",
    "update_meeting",
    "get_event_details",
    "add_attendees_to_event",
    "create_task",
    "list_tasks",
    "complete_task",
    "delete_task",
    "update_task",
    "get_upcoming_deadlines",
    "search_knowledge_base",
    "web_search",
    "search_news",
]
