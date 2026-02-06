"""Testes para outros agents (web_search, knowledge, general_chat, summary, automation, router)"""
import pytest
from unittest.mock import Mock, patch


# ============= WEB SEARCH AGENT =============
@patch('src.agents.web_search_agent.ChatOpenAI')
def test_web_search_agent_init(mock_llm):
    from src.agents.web_search_agent import WebSearchAgent
    mock_llm.return_value = Mock()
    agent = WebSearchAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


@patch('src.agents.web_search_agent.web_search')
@patch('src.agents.web_search_agent.ChatOpenAI')
def test_web_search_agent_process_web(mock_llm, mock_search):
    from src.agents.web_search_agent import WebSearchAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content='{"search_type": "web", "query": "python programming", "max_results": 3}'
    ))
    mock_llm.return_value = mock_llm_instance
    
    mock_search.return_value = {"status": "success", "message": "Found 3 results"}
    
    agent = WebSearchAgent()
    state = {
        "messages": [HumanMessage(content="Search for python programming")],
        "agent": "web_search"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.web_search_agent.search_news')
@patch('src.agents.web_search_agent.ChatOpenAI')
def test_web_search_agent_process_news(mock_llm, mock_news):
    from src.agents.web_search_agent import WebSearchAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content='{"search_type": "news", "query": "AI news", "max_results": 1}'
    ))
    mock_llm.return_value = mock_llm_instance
    
    mock_news.return_value = {"status": "success", "message": "Latest AI news"}
    
    agent = WebSearchAgent()
    state = {
        "messages": [HumanMessage(content="Latest AI news")],
        "agent": "web_search"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.web_search_agent.ChatOpenAI')
def test_web_search_agent_process_invalid_json(mock_llm):
    from src.agents.web_search_agent import WebSearchAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content='invalid json'))
    mock_llm.return_value = mock_llm_instance
    
    agent = WebSearchAgent()
    state = {
        "messages": [HumanMessage(content="Search something")],
        "agent": "web_search"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.web_search_agent.ChatOpenAI')
def test_web_search_agent_process_error(mock_llm):
    from src.agents.web_search_agent import WebSearchAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(side_effect=Exception("API Error"))
    mock_llm.return_value = mock_llm_instance
    
    agent = WebSearchAgent()
    state = {
        "messages": [HumanMessage(content="Search")],
        "agent": "web_search"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


# ============= KNOWLEDGE AGENT =============
@patch('src.agents.knowledge_agent.ChatOpenAI')
def test_knowledge_agent_init(mock_llm):
    from src.agents.knowledge_agent import KnowledgeAgent
    mock_llm.return_value = Mock()
    agent = KnowledgeAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


@patch('src.agents.knowledge_agent.search_knowledge_base')
@patch('src.agents.knowledge_agent.ChatOpenAI')
def test_knowledge_agent_process_with_results(mock_llm, mock_search):
    from src.agents.knowledge_agent import KnowledgeAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="Here is the answer based on documents"))
    mock_llm.return_value = mock_llm_instance
    
    mock_search.return_value = {
        "status": "success",
        "results": ["Document 1 content about company", "Document 2 about policies"]
    }
    
    agent = KnowledgeAgent()
    state = {
        "messages": [HumanMessage(content="What are the company policies?")],
        "agent": "knowledge"
    }
    
    result = agent.process(state)
    assert hasattr(agent, 'llm')


@patch('src.agents.general_chat_agent.ChatOpenAI')
def test_general_chat_agent_process(mock_llm):
    from src.agents.general_chat_agent import GeneralChatAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="Hello! How can I help you today?"))
    mock_llm.return_value = mock_llm_instance
    
    agent = GeneralChatAgent()
    state = {
        "messages": [HumanMessage(content="Hi there!")],
        "agent": "general_chat"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result
    assert result["response"] == "Hello! How can I help you today?"


@patch('src.agents.general_chat_agent.ChatOpenAI')
def test_general_chat_agent_process_with_history(mock_llm):
    from src.agents.general_chat_agent import GeneralChatAgent
    from langchain_core.messages import HumanMessage, AIMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="Sure, I remember!"))
    mock_llm.return_value = mock_llm_instance
    
    agent = GeneralChatAgent()
    state = {
        "messages": [
            HumanMessage(content="My name is John"),
            AIMessage(content="Nice to meet you John!"),
            HumanMessage(content="What is my name?")
        ],
        "agent": "general_chat"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.general_chat_agent.ChatOpenAI')
def test_general_chat_agent_process_error(mock_llm):
    from src.agents.general_chat_agent import GeneralChatAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(side_effect=Exception("API Error"))
    mock_llm.return_value = mock_llm_instance
    
    agent = GeneralChatAgent()
    state = {
        "messages": [HumanMessage(content="Hello")],
        "agent": "general_chat"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


# ============= KNOWLEDGE AGENT =============
@patch('src.agents.knowledge_agent.ChatOpenAI')
def test_knowledge_agent_init(mock_llm):
    from src.agents.knowledge_agent import KnowledgeAgent
    mock_llm.return_value = Mock()
    agent = KnowledgeAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


@patch('src.agents.knowledge_agent.search_knowledge_base')
@patch('src.agents.knowledge_agent.ChatOpenAI')
def test_knowledge_agent_process_with_results(mock_llm, mock_search):
    from src.agents.knowledge_agent import KnowledgeAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="Here is the answer based on documents"))
    mock_llm.return_value = mock_llm_instance
    
    mock_search.return_value = {
        "status": "success",
        "results": ["Document 1 content about company", "Document 2 about policies"]
    }
    
    agent = KnowledgeAgent()
    state = {
        "messages": [HumanMessage(content="What are the company policies?")],
        "agent": "knowledge"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.knowledge_agent.web_search')
@patch('src.agents.knowledge_agent.search_knowledge_base')
@patch('src.agents.knowledge_agent.ChatOpenAI')
def test_knowledge_agent_process_fallback_to_web(mock_llm, mock_kb, mock_web):
    from src.agents.knowledge_agent import KnowledgeAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="Here is what I found online"))
    mock_llm.return_value = mock_llm_instance
    
    # No results from knowledge base
    mock_kb.return_value = {"status": "success", "results": []}
    
    # Web search returns results
    mock_web.return_value = {"status": "success", "message": "Web results"}
    
    agent = KnowledgeAgent()
    state = {
        "messages": [HumanMessage(content="Tell me about AI")],
        "agent": "knowledge"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.knowledge_agent.search_knowledge_base')
@patch('src.agents.knowledge_agent.ChatOpenAI')
def test_knowledge_agent_process_error(mock_llm, mock_search):
    from src.agents.knowledge_agent import KnowledgeAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_search.return_value = {"status": "error", "message": "Database error"}
    
    agent = KnowledgeAgent()
    state = {
        "messages": [HumanMessage(content="Search something")],
        "agent": "knowledge"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


# ============= GENERAL CHAT AGENT =============
@patch('src.agents.general_chat_agent.ChatOpenAI')
def test_general_chat_agent_init(mock_llm):
    from src.agents.general_chat_agent import GeneralChatAgent
    mock_llm.return_value = Mock()
    agent = GeneralChatAgent()
    assert agent is not None


@patch('src.agents.general_chat_agent.ChatOpenAI')
def test_general_chat_agent_respond(mock_llm):
    from src.agents.general_chat_agent import GeneralChatAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="Hello! How can I help?"))
    mock_llm.return_value = mock_llm_instance
    
    agent = GeneralChatAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


# ============= SUMMARY AGENT =============
@patch('src.agents.summary_agent.ChatOpenAI')
def test_summary_agent_init(mock_llm):
    from src.agents.summary_agent import SummaryAgent
    mock_llm.return_value = Mock()
    agent = SummaryAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


@patch('src.agents.summary_agent.ChatOpenAI')
def test_summary_agent_count_tokens(mock_llm):
    from src.agents.summary_agent import SummaryAgent
    from langchain_core.messages import HumanMessage, AIMessage
    
    mock_llm.return_value = Mock()
    agent = SummaryAgent()
    
    messages = [
        HumanMessage(content="Hello there"),
        AIMessage(content="Hi! How can I help?")
    ]
    
    token_count = agent.count_tokens(messages)
    assert token_count > 0
    assert isinstance(token_count, int)


@patch('src.agents.summary_agent.ChatOpenAI')
def test_summary_agent_summarize(mock_llm):
    from src.agents.summary_agent import SummaryAgent
    from langchain_core.messages import HumanMessage, AIMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content="Summary: User asked about Python, assistant explained basics."
    ))
    mock_llm.return_value = mock_llm_instance
    
    agent = SummaryAgent()
    messages = [
        HumanMessage(content="Tell me about Python"),
        AIMessage(content="Python is a programming language...")
    ]
    
    summary = agent.summarize_messages(messages)
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0


@patch('src.agents.summary_agent.ChatOpenAI')
def test_summary_agent_summarize_with_existing(mock_llm):
    from src.agents.summary_agent import SummaryAgent
    from langchain_core.messages import HumanMessage, AIMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content="Updated summary with new context."
    ))
    mock_llm.return_value = mock_llm_instance
    
    agent = SummaryAgent()
    messages = [
        HumanMessage(content="More questions"),
        AIMessage(content="More answers")
    ]
    
    summary = agent.summarize_messages(messages, existing_summary="Previous chat about Python")
    assert summary is not None
    assert isinstance(summary, str)


# ============= AUTOMATION AGENT =============
@patch('src.agents.automation_agent.ChatOpenAI')
def test_automation_agent_init(mock_llm):
    from src.agents.automation_agent import AutomationAgent
    mock_llm.return_value = Mock()
    agent = AutomationAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


# ============= ROUTER AGENT =============
@patch('src.agents.router_agent.ChatOpenAI')
def test_router_agent_init(mock_llm):
    from src.agents.router_agent import RouterAgent
    mock_llm.return_value = Mock()
    agent = RouterAgent()
    assert agent is not None
    assert hasattr(agent, 'llm')


@patch('src.agents.router_agent.ChatOpenAI')
def test_router_agent_determine_intent_calendar(mock_llm):
    from src.agents.router_agent import RouterAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="schedule_meeting"))
    mock_llm.return_value = mock_llm_instance
    
    agent = RouterAgent()
    state = {
        "messages": [HumanMessage(content="Schedule a meeting tomorrow")],
        "agent": "router"
    }
    
    result = agent.determine_intent(state)
    assert result is not None
    assert "intent" in result


@patch('src.agents.router_agent.ChatOpenAI')
def test_router_agent_determine_intent_pending_meeting(mock_llm):
    from src.agents.router_agent import RouterAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm.return_value = Mock()
    
    agent = RouterAgent()
    state = {
        "messages": [HumanMessage(content="Yes, reschedule")],
        "pending_meeting": {"title": "Test Meeting"},
        "agent": "router"
    }
    
    result = agent.determine_intent(state)
    assert result is not None
    assert result["intent"] == "schedule_meeting"


@patch('src.agents.router_agent.ChatOpenAI')
def test_router_agent_determine_intent_web_search(mock_llm):
    from src.agents.router_agent import RouterAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="web_search"))
    mock_llm.return_value = mock_llm_instance
    
    agent = RouterAgent()
    state = {
        "messages": [HumanMessage(content="Latest news about AI")],
        "agent": "router"
    }
    
    result = agent.determine_intent(state)
    assert result is not None
    assert "intent" in result


@patch('src.agents.router_agent.ChatOpenAI')
def test_router_agent_determine_intent_task_management(mock_llm):
    from src.agents.router_agent import RouterAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="task_management"))
    mock_llm.return_value = mock_llm_instance
    
    agent = RouterAgent()
    state = {
        "messages": [HumanMessage(content="Create task to buy milk")],
        "agent": "router"
    }
    
    result = agent.determine_intent(state)
    assert result is not None
    assert "intent" in result


# ============= INTEGRATION MODULE =============
def test_integration_module_imports():
    """Test that all integration functions can be imported"""
    from src.agents import integration
    assert integration is not None
    assert hasattr(integration, '__name__')
