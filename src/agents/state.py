"""State definition for the chatbot agent graph."""
from typing import Annotated, Sequence, TypedDict
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
