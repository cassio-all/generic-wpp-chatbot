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
- "knowledge_query": User is asking a question that might be answered from the knowledge base (internal documents)
- "schedule_meeting": User wants to schedule a meeting or event, list calendar, cancel/edit meetings
- "send_email": User wants to send, read, or search emails
- "task_management": User wants to manage tasks (TODO list): create, list, complete, delete tasks
- "web_search": User wants to search the internet, get current information, news, weather, real-time data, or any information that requires internet search
- "general_chat": General conversation, greeting, or unclear intent

IMPORTANT: Choose "task_management" for:
- Creating tasks, TODO items, reminders
- Listing tasks, seeing what's pending
- Completing tasks, marking as done
- Deleting tasks, removing from list
- Task deadlines, priorities
- "criar tarefa", "adicionar no TODO", "listar tarefas"
- "completar tarefa", "marcar como feita"
- "deletar tarefa", "remover"

IMPORTANT: Choose "web_search" for:
- News, current events, today's information
- Weather, climate, temperature
- Latest updates, recent happenings
- Prices, stocks, cryptocurrency
- Sports scores, results
- Any question starting with "what is", "tell me about", "search for"
- Questions about current/recent events
- "Notícias", "novidades", "últimas"

Examples:
- "criar tarefa comprar leite" -> task_management
- "listar minhas tarefas" -> task_management
- "completar tarefa de estudar" -> task_management
- "me fale a principal notícia de hoje" -> web_search (news, today)
- "notícias sobre IA" -> web_search (news)
- "qual o clima em SP?" -> web_search (weather)
- "o que é Python?" -> web_search (requires search)
- "agende reunião" -> schedule_meeting
- "liste meus eventos" -> schedule_meeting
- "envie email" -> send_email
- "ler meus emails" -> send_email
- "oi, tudo bem?" -> general_chat

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
