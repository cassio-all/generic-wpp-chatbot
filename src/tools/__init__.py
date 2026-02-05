"""Tools package for the chatbot."""
from .email_tool import send_email
from .calendar_tool import (
    schedule_meeting,
    list_upcoming_events,
    check_conflicts,
    find_available_slots,
    cancel_meeting,
    update_meeting
)
from .knowledge_tool import search_knowledge_base

__all__ = [
    "send_email",
    "schedule_meeting",
    "list_upcoming_events",
    "check_conflicts",
    "find_available_slots",
    "cancel_meeting",
    "update_meeting",
    "search_knowledge_base",
]
