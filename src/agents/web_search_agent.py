"""Web search agent for searching the internet."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState
from src.tools.web_search_tool import web_search, search_news
import structlog
import json
import re

logger = structlog.get_logger()


class WebSearchAgent:
    """Agent responsible for web searches."""
    
    def __init__(self):
        """Initialize the web search agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process a web search request.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with search results
        """
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        logger.info("Processing web search request", message=last_message[:50])
        
        # Determine if it's a news search or general search
        system_prompt = """Você é um assistente de pesquisa na web. Analise a mensagem do usuário e determine:

1. Se é uma busca de notícias (news) ou busca geral (web)
2. Extraia a query de busca apropriada
3. Quantos resultados o usuário quer (1-5)

Responda APENAS com um JSON no formato:
{
  "search_type": "news" ou "web",
  "query": "query de busca otimizada",
  "max_results": número de 1 a 5,
  "reason": "breve explicação"
}

Dicas para max_results:
- "principal notícia", "a notícia", "o que aconteceu" = 1
- "algumas notícias", "me fale sobre" = 3
- "pesquise", "busque", "procure" = 5

Exemplos:
- "principal notícia sobre IA" -> {"search_type": "news", "query": "inteligência artificial", "max_results": 1}
- "notícias sobre Python" -> {"search_type": "news", "query": "Python programming", "max_results": 3}
- "o que é Python?" -> {"search_type": "web", "query": "Python programming language", "max_results": 3}"""
        
        try:
            # Analyze the query
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Mensagem do usuário: {last_message}")
            ])
            
            # Extract JSON
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if not json_match:
                state["response"] = "Desculpe, não consegui processar sua busca. Pode reformular?"
                return state
            
            search_info = json.loads(json_match.group())
            search_type = search_info.get("search_type", "web")
            query = search_info.get("query", last_message)
            max_results = min(search_info.get("max_results", 3), 5)  # Limitar a 5
            
            logger.info("Search parameters", 
                       search_type=search_type, 
                       query=query, 
                       max_results=max_results)
            
            # Perform search
            if search_type == "news":
                result = search_news(query, max_results=max_results)
            else:
                result = web_search(query, max_results=max_results)
            
            if result["status"] == "error":
                # User-friendly error message
                if "Aguarde alguns segundos" in result['message']:
                    response_text = result['message']
                else:
                    response_text = f"❌ Não consegui fazer a busca no momento. Tente novamente em alguns segundos ou reformule sua pergunta."
            elif not result["results"]:
                response_text = f"🔍 Não encontrei resultados para: **{query}**\n\nTente reformular sua busca."
            else:
                # Sempre deixar o LLM formatar a resposta de forma inteligente
                format_prompt = f"""Você é um assistente que apresenta resultados de busca de forma clara e contextualizada.

PEDIDO DO USUÁRIO: "{last_message}"

RESULTADOS DA BUSCA (query: {query}):
{json.dumps(result['results'], ensure_ascii=False, indent=2)}

INSTRUÇÕES:
1. Analise o que o usuário REALMENTE quer saber
2. Se pediu "principal" ou "resumo", forneça contexto e explique a relevância
3. Se pediu múltiplas notícias, resuma cada uma brevemente
4. Se é busca geral, explique o conceito/responda a pergunta diretamente
5. Seja conciso mas informativo
6. SEMPRE inclua as fontes (títulos e URLs) ao final

FORMATO DA RESPOSTA:
- Use markdown para estruturar
- Emojis apropriados (📰 para notícias, 💡 para insights, 🔍 para pesquisas)
- Links clicáveis: [Título](URL)
- Datas quando relevante

Responda de forma natural e útil:"""
                
                formatted_response = self.llm.invoke([
                    SystemMessage(content="Você é um assistente de pesquisa que apresenta informações de forma clara, contextualizada e útil."),
                    HumanMessage(content=format_prompt)
                ])
                
                response_text = formatted_response.content
            
            state["response"] = response_text
            state["messages"] = state["messages"] + [AIMessage(content=response_text)]
            
            logger.info("Web search processed", 
                       search_type=search_type,
                       num_results=len(result.get("results", [])))
            
        except Exception as e:
            logger.error("Error processing web search", error=str(e))
            state["response"] = "Desculpe, ocorreu um erro ao realizar a busca. Por favor, tente novamente."
        
        return state
