"""Tests for the chatbot agents."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.orchestrator import ChatbotOrchestrator
from src.agents.state import AgentState
from langchain_core.messages import HumanMessage


class TestChatbotOrchestrator:
    """Test the main chatbot orchestrator."""
    
    @patch('src.agents.router_agent.ChatOpenAI')
    @patch('src.agents.general_chat_agent.ChatOpenAI')
    def test_orchestrator_initialization(self, mock_chat_llm, mock_router_llm):
        """Test that orchestrator initializes correctly."""
        orchestrator = ChatbotOrchestrator()
        
        assert orchestrator is not None
        assert orchestrator.router_agent is not None
        assert orchestrator.knowledge_agent is not None
        assert orchestrator.calendar_agent is not None
        assert orchestrator.email_agent is not None
        assert orchestrator.general_chat_agent is not None
        assert orchestrator.graph is not None
    
    @patch('src.agents.router_agent.ChatOpenAI')
    @patch('src.agents.general_chat_agent.ChatOpenAI')
    def test_process_general_chat_message(self, mock_chat_llm, mock_router_llm):
        """Test processing a general chat message."""
        # Mock LLM responses
        mock_router_response = Mock()
        mock_router_response.content = "general_chat"
        mock_router_llm.return_value.invoke.return_value = mock_router_response
        
        mock_chat_response = Mock()
        mock_chat_response.content = "Olá! Como posso ajudar?"
        mock_chat_llm.return_value.invoke.return_value = mock_chat_response
        
        orchestrator = ChatbotOrchestrator()
        response = orchestrator.process_message("Olá", "test_user")
        
        assert response is not None
        assert isinstance(response, str)


class TestAgentState:
    """Test the agent state structure."""
    
    def test_agent_state_structure(self):
        """Test that agent state has required fields."""
        state: AgentState = {
            "messages": [HumanMessage(content="Test")],
            "intent": "test",
            "sender": "user",
            "should_use_tools": False,
            "response": ""
        }
        
        assert "messages" in state
        assert "intent" in state
        assert "sender" in state
        assert "should_use_tools" in state
        assert "response" in state
