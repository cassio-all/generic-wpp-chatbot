"""Knowledge base retrieval tool."""
from typing import List
from src.services import KnowledgeBaseService
import structlog

logger = structlog.get_logger()

# Global knowledge base service instance
_kb_service = None


def get_kb_service() -> KnowledgeBaseService:
    """Get or create knowledge base service instance."""
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service


def search_knowledge_base(query: str, max_results: int = 3) -> dict:
    """Search the knowledge base for relevant information.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with status and search results
    """
    try:
        kb_service = get_kb_service()
        results = kb_service.search(query, k=max_results)
        
        logger.info("Knowledge base search completed", query=query, num_results=len(results))
        
        if not results:
            return {
                "status": "success",
                "message": "No relevant information found in knowledge base",
                "results": []
            }
        
        return {
            "status": "success",
            "results": results,
            "message": f"Found {len(results)} relevant document(s)"
        }
        
    except Exception as e:
        logger.error("Error searching knowledge base", error=str(e), query=query)
        return {
            "status": "error",
            "message": f"Failed to search knowledge base: {str(e)}",
            "results": []
        }
