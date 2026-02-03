"""Router agent for determining user intent and routing to appropriate sub-agent."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings
from src.agents.state import AgentState
import structlog

logger = structlog.get_logger()


class RouterAgent:
    """Agent responsible for routing user requests to appropriate handlers."""
    
    def __init__(self):
        """Initialize the router agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
    
    def determine_intent(self, state: AgentState) -> AgentState:
        """Determine the user's intent from their message.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with intent
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Check if user is in the middle of a conversation flow
        # If there's a pending_meeting, they're responding to calendar conflict resolution
        if state.get("pending_meeting") or state.get("awaiting_reschedule_time"):
            logger.info("Detected pending calendar interaction, routing to calendar agent")
            state["intent"] = "schedule_meeting"
            state["should_use_tools"] = True
            return state
        
        system_prompt = """You are a router agent. Analyze the user's message and determine their intent.
        
Available intents:
- "knowledge_query": User is asking a question that might be answered from the knowledge base
- "schedule_meeting": User wants to schedule a meeting or event
- "send_email": User wants to send an email
- "general_chat": General conversation, greeting, or unclear intent

Respond with ONLY the intent name, nothing else."""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User message: {last_message}")
            ])
            
            intent = response.content.strip().lower()
            logger.info("Intent determined", intent=intent, message=last_message[:50])
            
            state["intent"] = intent
            state["should_use_tools"] = intent != "general_chat"
            
        except Exception as e:
            logger.error("Error determining intent", error=str(e))
            state["intent"] = "general_chat"
            state["should_use_tools"] = False
        
        return state
