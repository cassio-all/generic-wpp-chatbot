"""Web search tool using DuckDuckGo."""
from typing import Optional
from duckduckgo_search import DDGS
import structlog

logger = structlog.get_logger()


def web_search(
    query: str,
    max_results: int = 5,
    region: str = "br-pt"
) -> dict:
    """Search the web using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        region: Region code (default: br-pt for Brazil Portuguese)
        
    Returns:
        Dictionary with status and results
    """
    try:
        logger.info("Performing web search", query=query[:50], max_results=max_results)
        
        with DDGS() as ddgs:
            results = list(ddgs.text(
                keywords=query,
                region=region,
                max_results=max_results,
                safesearch='moderate',
                timelimit=None
            ))
        
        if not results:
            return {
                "status": "success",
                "message": "Não encontrei resultados para essa busca. Tente reformular a pergunta.",
                "results": []
            }
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("href", ""),
            })
        
        logger.info("Web search completed", num_results=len(formatted_results))
        
        return {
            "status": "success",
            "message": f"Found {len(formatted_results)} results",
            "results": formatted_results,
            "query": query
        }
    
    except Exception as e:
        error_msg = str(e)
        
        # Better error messages for common issues
        if "403" in error_msg or "Ratelimit" in error_msg:
            logger.warning("Rate limit hit on web search", query=query)
            return {
                "status": "error",
                "message": "Desculpe, muitas buscas recentes. Aguarde alguns segundos e tente novamente, ou reformule sua pergunta.",
                "results": []
            }
        
        logger.error("Error performing web search", error=error_msg, query=query)
        return {
            "status": "error",
            "message": f"Não consegui fazer a busca no momento. Erro: {error_msg[:100]}",
            "results": []
        }


def search_news(
    query: str,
    max_results: int = 5,
    region: str = "br-pt"
) -> dict:
    """Search for news using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        region: Region code
        
    Returns:
        Dictionary with status and news results
    """
    try:
        logger.info("Performing news search", query=query[:50])
        
        with DDGS() as ddgs:
            results = list(ddgs.news(
                keywords=query,
                region=region,
                max_results=max_results
            ))
        
        if not results:
            return {
                "status": "success",
                "message": "No news found",
                "results": []
            }
        
        # Format news results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("url", ""),
                "date": r.get("date", ""),
                "source": r.get("source", "")
            })
        
        logger.info("News search completed", num_results=len(formatted_results))
        
        return {
            "status": "success",
            "message": f"Found {len(formatted_results)} news articles",
            "results": formatted_results,
            "query": query
        }
    
    except Exception as e:
        logger.error("Error performing news search", error=str(e))
        return {
            "status": "error",
            "message": f"News search failed: {str(e)}",
            "results": []
        }
