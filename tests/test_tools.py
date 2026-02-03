"""Tests for the chatbot tools."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.tools.knowledge_tool import search_knowledge_base
from src.tools.email_tool import send_email
from src.tools.calendar_tool import schedule_meeting


class TestKnowledgeTool:
    """Test the knowledge base search tool."""
    
    @patch('src.tools.knowledge_tool.get_kb_service')
    def test_search_knowledge_base_success(self, mock_kb_service):
        """Test successful knowledge base search."""
        mock_service = Mock()
        mock_service.search.return_value = ["Result 1", "Result 2"]
        mock_kb_service.return_value = mock_service
        
        result = search_knowledge_base("test query")
        
        assert result["status"] == "success"
        assert len(result["results"]) == 2
        mock_service.search.assert_called_once_with("test query", k=3)
    
    @patch('src.tools.knowledge_tool.get_kb_service')
    def test_search_knowledge_base_no_results(self, mock_kb_service):
        """Test knowledge base search with no results."""
        mock_service = Mock()
        mock_service.search.return_value = []
        mock_kb_service.return_value = mock_service
        
        result = search_knowledge_base("test query")
        
        assert result["status"] == "success"
        assert len(result["results"]) == 0
        assert "No relevant information" in result["message"]


class TestEmailTool:
    """Test the email sending tool."""
    
    @patch('src.tools.email_tool.SendGridAPIClient')
    @patch('src.tools.email_tool.settings')
    def test_send_email_success(self, mock_settings, mock_sg_client):
        """Test successful email sending."""
        mock_settings.sendgrid_api_key = "test_key"
        mock_settings.sender_email = "sender@test.com"
        
        mock_response = Mock()
        mock_response.status_code = 202
        mock_sg_client.return_value.send.return_value = mock_response
        
        result = send_email(
            to_email="recipient@test.com",
            subject="Test",
            content="Test content"
        )
        
        assert result["status"] == "success"
        assert "sent successfully" in result["message"]
    
    @patch('src.tools.email_tool.settings')
    def test_send_email_no_api_key(self, mock_settings):
        """Test email sending without API key."""
        mock_settings.sendgrid_api_key = None
        
        result = send_email(
            to_email="recipient@test.com",
            subject="Test",
            content="Test content"
        )
        
        assert result["status"] == "error"
        assert "not configured" in result["message"]


class TestCalendarTool:
    """Test the calendar scheduling tool."""
    
    @patch('src.tools.calendar_tool.get_calendar_service')
    def test_schedule_meeting_no_service(self, mock_service):
        """Test meeting scheduling without calendar service."""
        mock_service.return_value = None
        
        result = schedule_meeting(
            summary="Test Meeting",
            start_time="2024-03-20T10:00:00",
            duration_minutes=60
        )
        
        assert result["status"] == "error"
        assert "not configured" in result["message"]
