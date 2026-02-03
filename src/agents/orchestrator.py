"""Main orchestrator using LangGraph."""
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from src.agents.state import AgentState
from src.agents.router_agent import RouterAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.calendar_agent import CalendarAgent
from src.agents.email_agent import EmailAgent
from src.agents.general_chat_agent import GeneralChatAgent
import structlog

logger = structlog.get_logger()


class ChatbotOrchestrator:
    """Main orchestrator for the chatbot using LangGraph."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.router_agent = RouterAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.calendar_agent = CalendarAgent()
        self.email_agent = EmailAgent()
        self.general_chat_agent = GeneralChatAgent()
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self.router_agent.determine_intent)
        workflow.add_node("knowledge", self.knowledge_agent.process)
        workflow.add_node("calendar", self.calendar_agent.process)
        workflow.add_node("email", self.email_agent.process)
        workflow.add_node("general_chat", self.general_chat_agent.process)
        
        # Define routing logic
        def route_by_intent(state: AgentState) -> Literal["knowledge", "calendar", "email", "general_chat"]:
            """Route to appropriate agent based on intent."""
            intent = state.get("intent", "general_chat")
            
            if intent == "knowledge_query":
                return "knowledge"
            elif intent == "schedule_meeting":
                return "calendar"
            elif intent == "send_email":
                return "email"
            else:
                return "general_chat"
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add conditional edges from router
        workflow.add_conditional_edges(
            "router",
            route_by_intent,
            {
                "knowledge": "knowledge",
                "calendar": "calendar",
                "email": "email",
                "general_chat": "general_chat",
            }
        )
        
        # All agents end after processing
        workflow.add_edge("knowledge", END)
        workflow.add_edge("calendar", END)
        workflow.add_edge("email", END)
        workflow.add_edge("general_chat", END)
        
        return workflow.compile()
    
    def process_message(self, message: str, sender: str = "user") -> str:
        """Process a message through the agent graph.
        
        Args:
            message: The message to process
            sender: The sender identifier
            
        Returns:
            The response message
        """
        logger.info("Processing message", sender=sender, message=message[:50])
        
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "intent": "",
            "sender": sender,
            "should_use_tools": False,
            "response": ""
        }
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            response = final_state.get("response", "Desculpe, não consegui processar sua mensagem.")
            
            logger.info("Message processed successfully", response_length=len(response))
            
            return response
            
        except Exception as e:
            logger.error("Error processing message", error=str(e))
            return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
