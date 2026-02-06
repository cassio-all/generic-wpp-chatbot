"""Testes para src/tools/knowledge_tool.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.tools.knowledge_tool.KnowledgeBaseService')
def test_search_knowledge_base(mock_kb_service):
    from src.tools.knowledge_tool import search_knowledge_base
    mock_kb = Mock()
    mock_kb.search.return_value = ["Document 1", "Document 2"]
    mock_kb_service.return_value = mock_kb
    result = search_knowledge_base("test query", 5)
    assert result is not None


@patch('src.tools.knowledge_tool.KnowledgeBaseService')
def test_search_knowledge_base_empty(mock_kb_service):
    from src.tools.knowledge_tool import search_knowledge_base
    mock_kb = Mock()
    mock_kb.search.return_value = []
    mock_kb_service.return_value = mock_kb
    result = search_knowledge_base("nonexistent")
    assert result is not None
