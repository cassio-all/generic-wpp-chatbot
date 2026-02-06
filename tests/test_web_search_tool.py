"""Testes para src/tools/web_search_tool.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.tools.web_search_tool.DDGS')
def test_web_search(mock_ddgs):
    from src.tools.web_search_tool import web_search
    mock_ddgs_instance = Mock()
    mock_ddgs_instance.text.return_value = [{'title': 'Result', 'href': 'http://test', 'body': 'Body'}]
    mock_ddgs.return_value = mock_ddgs_instance
    result = web_search("test query", 5)
    assert result is not None


@patch('src.tools.web_search_tool.DDGS')
def test_web_search_with_region(mock_ddgs):
    from src.tools.web_search_tool import web_search
    mock_ddgs_instance = Mock()
    mock_ddgs_instance.text.return_value = []
    mock_ddgs.return_value = mock_ddgs_instance
    result = web_search("test", 3, region="br-pt")
    assert result is not None
