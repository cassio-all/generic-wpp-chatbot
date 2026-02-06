"""Tests for the ChatbotOrchestrator with LangGraph."""
import pytest
from unittest.mock import Mock, patch
from src.agents.orchestrator import ChatbotOrchestrator


class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""
    
    def test_orchestrator_loads_all_agents(self):
        """Test that orchestrator loads all required agents."""
        with patch('src.agents.knowledge_agent.KnowledgeBaseService'):
            orch = ChatbotOrchestrator()
            
            # Should have all agents initialized
            assert hasattr(orch, 'router_agent')
            assert hasattr(orch, 'knowledge_agent')
            assert hasattr(orch, 'calendar_agent')
            assert hasattr(orch, 'email_agent')
            assert hasattr(orch, 'task_agent')
            assert hasattr(orch, 'automation_agent')
            assert hasattr(orch, 'general_chat_agent')
            assert hasattr(orch, 'summary_agent')
            assert hasattr(orch, 'web_search_agent')
    
    def test_orchestrator_has_graph(self):
        """Test that orchestrator builds LangGraph."""
        with patch('src.agents.knowledge_agent.KnowledgeBaseService'):
            orch = ChatbotOrchestrator()
            
            # Should have graph and memory
            assert hasattr(orch, 'graph')
            assert hasattr(orch, 'memory')
            assert orch.graph is not None
            assert orch.memory is not None
    
    def test_orchestrator_has_persistence(self):
        """Test that orchestrator initializes SQLite persistence."""
        with patch('src.agents.knowledge_agent.KnowledgeBaseService'):
            orch = ChatbotOrchestrator()
            
            # Should have SQLite checkpointer
            assert hasattr(orch, 'memory')
            # Memory should be SqliteSaver
            assert 'SqliteSaver' in str(type(orch.memory))
