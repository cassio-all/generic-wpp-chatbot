"""Testes para src/agents/task_agent.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_init(mock_llm):
    from src.agents.task_agent import TaskAgent
    mock_llm.return_value = Mock()
    agent = TaskAgent()
    assert agent is not None
    assert agent.llm is not None


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_create(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="create"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Create a task to buy milk")
    assert result == "create"


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_list(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="list"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Show my tasks")
    assert result == "list"


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_complete(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="complete"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Mark task 1 as done")
    assert result == "complete"


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_delete(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="delete"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Delete task 3")
    assert result == "delete"


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_update(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="update"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Update task priority")
    assert result == "update"


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_deadlines(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="deadlines"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Show upcoming deadlines")
    assert result == "deadlines"


@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_detect_error_fallback(mock_llm):
    from src.agents.task_agent import TaskAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(side_effect=Exception("API Error"))
    mock_llm.return_value = mock_llm_instance
    
    agent = TaskAgent()
    result = agent._detect_action("Some message")
    assert result == "list"  # Default fallback


@patch('src.agents.task_agent.create_task')
@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_create_task(mock_llm, mock_create):
    from src.agents.task_agent import TaskAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(
        content='{"needs_info": false, "title": "Buy milk", "priority": "high"}'
    ))
    mock_llm.return_value = mock_llm_instance
    
    mock_create.return_value = {"status": "success", "task": {"id": 1, "title": "Buy milk"}}
    
    agent = TaskAgent()
    state = {
        "messages": [HumanMessage(content="Create task to buy milk with high priority")],
        "agent": "task"
    }
    
    result = agent._create_task(state)
    assert result is not None
    assert "response" in result or "messages" in result


@patch('src.agents.task_agent.list_tasks')
@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_list_tasks(mock_llm, mock_list):
    from src.agents.task_agent import TaskAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_list.return_value = {
        "status": "success",
        "message": "Task 1: Buy milk\nTask 2: Study Python"
    }
    
    agent = TaskAgent()
    state = {
        "messages": [HumanMessage(content="List my tasks")],
        "agent": "task"
    }
    
    result = agent._list_tasks(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.task_agent.complete_task')
@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_complete_task(mock_llm, mock_complete):
    from src.agents.task_agent import TaskAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content='{"task_id": 1}'))
    mock_llm.return_value = mock_llm_instance
    
    mock_complete.return_value = {"status": "success", "message": "Task completed"}
    
    agent = TaskAgent()
    state = {
        "messages": [HumanMessage(content="Complete task 1")],
        "agent": "task"
    }
    
    result = agent._complete_task(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.task_agent.delete_task')
@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_delete_task(mock_llm, mock_delete):
    from src.agents.task_agent import TaskAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content='{"task_id": 1}'))
    mock_llm.return_value = mock_llm_instance
    
    mock_delete.return_value = {"status": "success", "message": "Task deleted"}
    
    agent = TaskAgent()
    state = {
        "messages": [HumanMessage(content="Delete task 1")],
        "agent": "task"
    }
    
    result = agent._delete_task(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.task_agent.list_tasks')
@patch('src.agents.task_agent.ChatOpenAI')
def test_task_agent_delete_task_no_tasks(mock_llm, mock_list):
    from src.agents.task_agent import TaskAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_list.return_value = {
        "status": "success",
        "tasks": []
    }
    
    agent = TaskAgent()
    state = {
        "messages": [HumanMessage(content="Delete task")],
        "agent": "task"
    }
    
    result = agent._delete_task(state)
    assert result is not None
    assert "response" in result
