"""State definition for the chatbot agent graph."""
from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the chatbot agent graph."""
    
    # The conversation messages
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # The current user intent/action
    intent: str
    
    # The sender information
    sender: str
    
    # Whether tools should be called
    should_use_tools: bool
    
    # Final response to send back
    response: str
    
    # Conversation memory management
    conversation_summary: Optional[str]  # Summarized history
    message_count: int  # Total messages in conversation
    total_tokens: int  # Approximate token count
    
    # Calendar conflict resolution
    pending_meeting: Optional[dict]  # Meeting waiting for conflict resolution
    conflicting_events: Optional[list]  # List of conflicting events
    awaiting_reschedule_time: Optional[bool]  # Waiting for new time from user
    suggested_slots: Optional[list]  # Suggested alternative time slots
