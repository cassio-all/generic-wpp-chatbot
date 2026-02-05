"""Main orchestrator using LangGraph."""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage
from src.agents.state import AgentState
from src.agents.router_agent import RouterAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.calendar_agent import CalendarAgent
from src.agents.email_agent import EmailAgent
from src.agents.general_chat_agent import GeneralChatAgent
from src.agents.summary_agent import SummaryAgent
from src.agents.web_search_agent import WebSearchAgent
from src.config import settings
import structlog
import os

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
        self.summary_agent = SummaryAgent()
        self.web_search_agent = WebSearchAgent()
        
        # Ensure data directory exists
        os.makedirs("./data", exist_ok=True)
        
        # Initialize SQLite checkpointer for persistent conversation history
        # SqliteSaver is used synchronously (not async) and manages connections automatically
        # Conversations are stored in ./data/checkpoints.db and survive restarts
        import sqlite3
        conn = sqlite3.connect("./data/checkpoints.db", check_same_thread=False)
        self.memory = SqliteSaver(conn)
        logger.info("✅ SQLite persistence enabled - conversations survive restarts", db_path="./data/checkpoints.db")
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self.router_agent.determine_intent)
        workflow.add_node("knowledge", self.knowledge_agent.process)
        workflow.add_node("calendar", self.calendar_agent.process)
        workflow.add_node("email", self.email_agent.process)
        workflow.add_node("web_search", self.web_search_agent.process)
        workflow.add_node("general_chat", self.general_chat_agent.process)
        
        # Define routing logic
        def route_by_intent(state: AgentState) -> Literal["knowledge", "calendar", "email", "web_search", "general_chat"]:
            """Route to appropriate agent based on intent."""
            intent = state.get("intent", "general_chat")
            
            if intent == "knowledge_query":
                return "knowledge"
            elif intent == "schedule_meeting":
                return "calendar"
            elif intent == "send_email":
                return "email"
            elif intent == "web_search":
                return "web_search"
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
                "web_search": "web_search",
                "general_chat": "general_chat",
            }
        )
        
        # All agents end after processing
        workflow.add_edge("knowledge", END)
        workflow.add_edge("calendar", END)
        workflow.add_edge("email", END)
        workflow.add_edge("web_search", END)
        workflow.add_edge("general_chat", END)
        
        # Compile with memory checkpointer
        return workflow.compile(checkpointer=self.memory)
    
    def process_message(self, message: str, sender: str = "user", thread_id: str = "default") -> str:
        """Process a message through the agent graph with conversation memory.
        
        Args:
            message: The message to process
            sender: The sender identifier
            thread_id: Unique identifier for conversation thread
            
        Returns:
            The response message
        """
        logger.info("Processing message", 
                   sender=sender, 
                   thread_id=thread_id,
                   message=message[:50])
        
        # Configuration for this thread
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state to check history
        try:
            current_state = self.graph.get_state(config)
            existing_messages = current_state.values.get("messages", []) if current_state.values else []
            existing_summary = current_state.values.get("conversation_summary", "") if current_state.values else ""
        except:
            existing_messages = []
            existing_summary = ""
        
        # Check if we need to summarize history
        if settings.enable_conversation_summary and existing_messages:
            if self.summary_agent.should_summarize(
                existing_messages, 
                settings.max_history_tokens
            ):
                logger.info("Summarizing conversation history due to token limit")
                compressed_messages, new_summary = self.summary_agent.compress_history(
                    existing_messages,
                    existing_summary,
                    settings.keep_recent_messages
                )
                
                # Update state with compressed history
                initial_state: AgentState = {
                    "messages": compressed_messages + [HumanMessage(content=message)],
                    "intent": "",
                    "sender": sender,
                    "should_use_tools": False,
                    "response": "",
                    "conversation_summary": new_summary,
                    "message_count": len(existing_messages) + 1,
                    "total_tokens": self.summary_agent.count_tokens(compressed_messages)
                }
            else:
                # No summarization needed
                initial_state: AgentState = {
                    "messages": [HumanMessage(content=message)],
                    "intent": "",
                    "sender": sender,
                    "should_use_tools": False,
                    "response": "",
                    "conversation_summary": existing_summary,
                    "message_count": len(existing_messages) + 1,
                    "total_tokens": self.summary_agent.count_tokens(existing_messages)
                }
        else:
            # First message or summarization disabled
            initial_state: AgentState = {
                "messages": [HumanMessage(content=message)],
                "intent": "",
                "sender": sender,
                "should_use_tools": False,
                "response": "",
                "conversation_summary": "",
                "message_count": 1,
                "total_tokens": 0
            }
        
        try:
            # Run the graph with memory persistence
            final_state = self.graph.invoke(initial_state, config)
            
            response = final_state.get("response", "Desculpe, não consegui processar sua mensagem.")
            
            # Log conversation stats
            total_tokens = final_state.get("total_tokens", 0)
            message_count = final_state.get("message_count", 0)
            
            logger.info("Message processed successfully", 
                       response_length=len(response),
                       thread_id=thread_id,
                       message_count=message_count,
                       total_tokens=total_tokens)
            
            return response
            
        except Exception as e:
            logger.error("Error processing message", 
                        error=str(e),
                        thread_id=thread_id)
            return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
    
    def get_conversation_history(self, thread_id: str = "default") -> list:
        """Get conversation history for a thread.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            List of messages in the conversation
        """
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state = self.graph.get_state(config)
            return state.values.get("messages", []) if state.values else []
        except:
            return []
    
    def clear_conversation(self, thread_id: str = "default") -> None:
        """Clear conversation history for a thread.
        
        Args:
            thread_id: Thread identifier
        """
        logger.info("Clearing conversation history", thread_id=thread_id)
        # Note: MemorySaver doesn't have a direct clear method
        # New conversations will start fresh automatically
