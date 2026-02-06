"""Testes simplificados e funcionais para o projeto."""
import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestWhatsAppClient:
    """Tests for WhatsApp Client basic functionality."""
    
    def test_whatsapp_client_initialization(self):
        """Test that WhatsApp client can be initialized."""
        from src.integrations.whatsapp_integration import WhatsAppClient
        
        # WhatsAppClient doesn't need orchestrator in __init__, only for message handling
        client = WhatsAppClient()
        
        assert hasattr(client, 'openai_client')
        assert hasattr(client, 'paused_contacts')
        assert hasattr(client, 'pause_duration')


class TestOrchestrator:
    """Tests for ChatbotOrchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes all agents."""
        from src.agents.orchestrator import ChatbotOrchestrator
        
        with patch('src.services.knowledge_base_faiss.KnowledgeBaseService'):
            orch = ChatbotOrchestrator()
            
            # All agents should be initialized
            assert orch.router_agent is not None
            assert orch.knowledge_agent is not None
            assert orch.calendar_agent is not None
            assert orch.email_agent is not None
            assert orch.task_agent is not None
            assert orch.automation_agent is not None
            assert orch.general_chat_agent is not None
            assert orch.summary_agent is not None
            assert orch.web_search_agent is not None
            
            # Should have graph and memory
            assert orch.graph is not None
            assert orch.memory is not None


class TestKnowledgeBase:
    """Tests for Knowledge Base FAISS service."""
    
    def test_knowledge_base_initialization(self):
        """Test that knowledge base initializes correctly."""
        from src.services.knowledge_base_faiss import KnowledgeBaseService
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.services.knowledge_base_faiss.settings') as mock_settings:
                mock_settings.knowledge_base_path = tmpdir
                mock_settings.vector_db_path = tmpdir
                mock_settings.openai_api_key = "test_key"
                
                kb = KnowledgeBaseService()
                
                # Should have initialization
                assert hasattr(kb, 'embeddings')
                assert hasattr(kb, 'files_hash')
    
    def test_knowledge_base_search_no_store(self):
        """Test search when no vector store exists."""
        from src.services.knowledge_base_faiss import KnowledgeBaseService
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.services.knowledge_base_faiss.settings') as mock_settings:
                mock_settings.knowledge_base_path = tmpdir
                mock_settings.vector_db_path = tmpdir
                mock_settings.openai_api_key = "test_key"
                
                kb = KnowledgeBaseService()
                kb.vector_store = None
                
                results = kb.search("test query")
                
                assert results == []


class TestAgents:
    """Tests for individual agents."""
    
    def test_router_agent_exists(self):
        """Test that router agent can be imported."""
        from src.agents.router_agent import RouterAgent
        
        agent = RouterAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    def test_knowledge_agent_exists(self):
        """Test that knowledge agent can be imported."""
        from src.agents.knowledge_agent import KnowledgeAgent
        
        agent = KnowledgeAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    def test_calendar_agent_exists(self):
        """Test that calendar agent can be imported."""
        from src.agents.calendar_agent import CalendarAgent
        
        agent = CalendarAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    def test_task_agent_exists(self):
        """Test that task agent can be imported."""
        from src.agents.task_agent import TaskAgent
        
        agent = TaskAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    def test_email_agent_exists(self):
        """Test that email agent can be imported."""
        from src.agents.email_agent import EmailAgent
        
        agent = EmailAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    def test_general_chat_agent_exists(self):
        """Test that general chat agent can be imported."""
        from src.agents.general_chat_agent import GeneralChatAgent
        
        agent = GeneralChatAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')
    
    def test_web_search_agent_exists(self):
        """Test that web search agent can be imported."""
        from src.agents.web_search_agent import WebSearchAgent
        
        agent = WebSearchAgent()
        assert agent is not None
        assert hasattr(agent, 'llm')


class TestTools:
    """Tests for tools functionality."""
    
    def test_knowledge_tool_import(self):
        """Test that knowledge tool can be imported."""
        from src.tools.knowledge_tool import search_knowledge_base
        
        assert callable(search_knowledge_base)
    
    def test_web_search_tool_import(self):
        """Test that web search tool can be imported."""
        from src.tools.web_search_tool import web_search
        
        assert callable(web_search)
    
    def test_calendar_tool_import(self):
        """Test that calendar tools can be imported."""
        from src.tools.calendar_tool import (
            schedule_meeting,
            list_upcoming_events,
            cancel_meeting,
            update_meeting
        )
        
        assert callable(schedule_meeting)
        assert callable(list_upcoming_events)
        assert callable(cancel_meeting)
        assert callable(update_meeting)
    
    def test_task_tool_import(self):
        """Test that task tools can be imported."""
        from src.tools.task_tool import (
            create_task,
            list_tasks,
            complete_task,
            delete_task
        )
        
        assert callable(create_task)
        assert callable(list_tasks)
        assert callable(complete_task)
        assert callable(delete_task)
    
    def test_email_tool_import(self):
        """Test that email tools can be imported."""
        from src.tools.email_tool import send_email, read_emails, search_emails
        
        assert callable(send_email)
        assert callable(read_emails)
        assert callable(search_emails)


class TestSettings:
    """Tests for settings configuration."""
    
    def test_settings_import(self):
        """Test that settings can be imported."""
        from src.config import settings
        
        assert settings is not None
        assert hasattr(settings, 'openai_api_key')


class TestState:
    """Tests for agent state."""
    
    def test_agent_state_import(self):
        """Test that AgentState can be imported."""
        from src.agents.state import AgentState
        
        # AgentState is a TypedDict, so we create it as a dict
        state: AgentState = {
            "messages": [],
            "next_agent": "test"
        }
        
        assert state is not None
        assert state["messages"] == []
        assert state["next_agent"] == "test"
