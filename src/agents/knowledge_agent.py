"""Knowledge agent for answering questions using the knowledge base."""
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools import search_knowledge_base, web_search
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
        
        # Check if results contain relevant information
        has_relevant_info = False
        if results:
            # Quick check: if all results are just generic system/welcome messages, consider as no results
            generic_phrases = [
                "chatbot genérico", "sistema de base de conhecimento inicializado", 
                "adicionar seus próprios arquivos", "arquivos suportados",
                "bem-vindo ao chatbot", "este é um chatbot genérico",
                "funcionalidades", "como usar", "personalização",
                "você pode fazer perguntas", "o chatbot usa inteligência"
            ]
            
            # Check if results have actual specific information
            relevant_results = []
            for r in results:
                r_lower = r.lower()
                # If result is mostly generic phrases, skip it
                generic_count = sum(1 for phrase in generic_phrases if phrase in r_lower)
                # If more than 20% of the text is generic OR it's very short with generic content
                if generic_count == 0 or (len(r) > 100 and generic_count < 2):
                    relevant_results.append(r)
            
            if relevant_results:
                has_relevant_info = True
                results = relevant_results  # Use only relevant results
            else:
                results = []  # Treat generic messages as no results
                logger.debug("Filtered out generic knowledge base content")
        
        if not results:
            # NO RELEVANT KNOWLEDGE FOUND → Try web search as fallback
            logger.info("No relevant knowledge base results, trying web search fallback", query=last_message)
            
            web_result = web_search(last_message, max_results=3)
            
            if web_result["status"] == "success" and web_result.get("results"):
                # Found on web! Format and return
                logger.info("Web search fallback successful", num_results=len(web_result["results"]))
                
                web_context = "\n\n".join([
                    f"**{r['title']}**\n{r['snippet']}\nFonte: {r['url']}" 
                    for r in web_result["results"]
                ])
                
                system_prompt = f"""Você é um assistente útil do WhatsApp.
A pergunta do usuário não estava na base de conhecimento local, mas encontrei informações na web.
Use os resultados abaixo para responder de forma clara e concisa.

DATA ATUAL: {datetime.now().strftime("%Y-%m-%d (%A, %d de %B de %Y)")}

IMPORTANTE: 
- Responda de forma natural, como se você soubesse a informação
- VALIDE datas e informações temporais contra a data atual
- Se a informação parecer desatualizada ou inconsistente, mencione isso
- Cite as fontes ao final se relevante
- Se perguntar sobre aniversário/data, responda apenas o DIA e MÊS (ex: "15 de março"), não invente anos ou contextos temporais"""
                
                try:
                    response = self.llm.invoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"Resultados da busca:\n{web_context}\n\nPergunta: {last_message}")
                    ])
                    
                    state["response"] = response.content
                    state["messages"] = state["messages"] + [AIMessage(content=response.content)]
                    logger.info("Knowledge query answered via web search fallback")
                    return state
                    
                except Exception as e:
                    logger.error("Error formatting web search results", error=str(e))
                    # Continue to "no info" response below
            
            # No results from knowledge base OR web search
            system_prompt = """Você é um assistente útil do WhatsApp. 
O usuário fez uma pergunta, mas não encontrei informações relevantes na base de conhecimento nem na internet.
Responda de forma educada que você não tem essas informações específicas no momento."""
            
            context = "Nenhuma informação relevante encontrada."
        else:
            system_prompt = f"""Você é um assistente útil do WhatsApp. 
Use as informações da base de conhecimento abaixo para responder à pergunta do usuário.

DATA ATUAL: {datetime.now().strftime("%Y-%m-%d (%A, %d de %B de %Y)")}

Seja claro, conciso e útil. Responda em português.
Se a pergunta envolver datas ou informações temporais, valide a consistência com a data atual."""
            
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
