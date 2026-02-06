"""Testes para src/agents/email_agent.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.agents.email_agent.ChatOpenAI')
def test_email_agent_init(mock_llm):
    from src.agents.email_agent import EmailAgent
    mock_llm.return_value = Mock()
    agent = EmailAgent()
    assert agent is not None
    assert agent.llm is not None


@patch('src.agents.email_agent.send_email')
@patch('src.agents.email_agent.ChatOpenAI')
def test_email_agent_process_send(mock_llm, mock_send):
    from src.agents.email_agent import EmailAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content='{"action": "send", "params": {"to_email": "test@example.com", "subject": "Test", "content": "Hello"}}'
    ))
    mock_llm.return_value = mock_llm_instance
    
    mock_send.return_value = {"status": "success", "message": "Email sent"}
    
    agent = EmailAgent()
    state = {
        "messages": [HumanMessage(content="Send email to test@example.com")],
        "agent": "email"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.email_agent.read_emails')
@patch('src.agents.email_agent.ChatOpenAI')
def test_email_agent_process_read(mock_llm, mock_read):
    from src.agents.email_agent import EmailAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content='{"action": "read", "params": {"max_emails": 5}}'
    ))
    mock_llm.return_value = mock_llm_instance
    
    mock_read.return_value = {"status": "success", "emails": []}
    
    agent = EmailAgent()
    state = {
        "messages": [HumanMessage(content="Read my latest emails")],
        "agent": "email"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.email_agent.search_emails')
@patch('src.agents.email_agent.ChatOpenAI')
def test_email_agent_process_search(mock_llm, mock_search):
    from src.agents.email_agent import EmailAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content='{"action": "search", "params": {"query": "important"}}'
    ))
    mock_llm.return_value = mock_llm_instance
    
    mock_search.return_value = {"status": "success", "results": []}
    
    agent = EmailAgent()
    state = {
        "messages": [HumanMessage(content="Search for important emails")],
        "agent": "email"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.email_agent.ChatOpenAI')
def test_email_agent_process_invalid_json(mock_llm):
    from src.agents.email_agent import EmailAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content='invalid json'))
    mock_llm.return_value = mock_llm_instance
    
    agent = EmailAgent()
    state = {
        "messages": [HumanMessage(content="Do something with email")],
        "agent": "email"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.email_agent.ChatOpenAI')
def test_email_agent_process_error(mock_llm):
    from src.agents.email_agent import EmailAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(side_effect=Exception("API Error"))
    mock_llm.return_value = mock_llm_instance
    
    agent = EmailAgent()
    state = {
        "messages": [HumanMessage(content="Send email")],
        "agent": "email"
    }
    
    result = agent.process(state)
    assert result is not None
    assert "response" in result
