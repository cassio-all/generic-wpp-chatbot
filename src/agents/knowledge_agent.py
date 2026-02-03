"""Knowledge agent for answering questions using the knowledge base."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools import search_knowledge_base
import structlog

logger = structlog.get_logger()


class KnowledgeAgent:
    """Agent responsible for answering questions using the knowledge base."""
    
    def __init__(self):
        """Initialize the knowledge agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process a knowledge query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing knowledge query", query=last_message[:50])
        
        # Search knowledge base
        search_result = search_knowledge_base(last_message, max_results=3)
        
        if search_result["status"] == "error":
            state["response"] = "Desculpe, tive um problema ao buscar informações. Por favor, tente novamente."
            return state
        
        results = search_result.get("results", [])
        
        if not results:
            system_prompt = """Você é um assistente útil do WhatsApp. 
O usuário fez uma pergunta, mas não encontrei informações relevantes na base de conhecimento.
Responda de forma educada que você não tem essas informações específicas no momento."""
            
            context = "Nenhuma informação relevante encontrada na base de conhecimento."
        else:
            system_prompt = """Você é um assistente útil do WhatsApp. 
Use as informações da base de conhecimento abaixo para responder à pergunta do usuário.
Seja claro, conciso e útil. Responda em português."""
            
            context = "\n\n".join([f"Documento {i+1}:\n{doc}" for i, doc in enumerate(results)])
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Contexto da base de conhecimento:\n{context}\n\nPergunta do usuário: {last_message}")
            ])
            
            state["response"] = response.content
            state["messages"] = state["messages"] + [AIMessage(content=response.content)]
            
            logger.info("Knowledge query processed successfully")
            
        except Exception as e:
            logger.error("Error processing knowledge query", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente."
        
        return state
