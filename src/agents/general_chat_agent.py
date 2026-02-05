"""General chat agent for conversations."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
import structlog

logger = structlog.get_logger()


class GeneralChatAgent:
    """Agent responsible for general conversation."""
    
    def __init__(self):
        """Initialize the general chat agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process a general chat message.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing general chat", message=last_message[:50])
        
        system_prompt = """Você é um assistente virtual amigável do WhatsApp. 
Responda de forma natural, educada e útil em português.
Se o usuário precisar de ajuda específica (agendar reuniões, enviar e-mails, buscar informações), 
oriente-o sobre como você pode ajudar."""
        
        try:
            # Build conversation history
            chat_messages = [SystemMessage(content=system_prompt)]
            
            # Add recent conversation history (last 5 messages)
            for msg in messages[-5:]:
                chat_messages.append(msg)
            
            response = self.llm.invoke(chat_messages)
            
            state["response"] = response.content
            state["messages"] = state["messages"] + [AIMessage(content=response.content)]
            
            logger.info("General chat processed successfully")
            
        except Exception as e:
            logger.error("Error processing general chat", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro. Por favor, tente novamente."
        
        return state
