"""Testes para src/agents/calendar_agent.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_init(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    mock_llm.return_value = Mock()
    agent = CalendarAgent()
    assert agent is not None
    assert agent.llm is not None


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_detect_schedule(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="schedule"))
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    result = agent._detect_action("Schedule a meeting tomorrow at 10am")
    assert result == "schedule"


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_detect_list(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="list"))
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    result = agent._detect_action("List my meetings")
    assert result == "list"


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_detect_cancel(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="cancel"))
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    result = agent._detect_action("Cancel the meeting")
    assert result == "cancel"


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_detect_edit(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="edit"))
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    result = agent._detect_action("Edit meeting time")
    assert result == "edit"


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_detect_details(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="details"))
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    result = agent._detect_action("Show meeting details")
    assert result == "details"


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_detect_error_fallback(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(side_effect=Exception("API Error"))
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    result = agent._detect_action("Some message")
    assert result == "schedule"  # Default fallback


@patch('src.agents.calendar_agent.schedule_meeting')
@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_reschedule(mock_llm, mock_schedule):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke = Mock(return_value=Mock(content="2024-03-21T14:00:00"))
    mock_llm.return_value = mock_llm_instance
    
    mock_schedule.return_value = {"status": "success", "message": "Rescheduled"}
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="Remanejar para 14h")],
        "conflicting_events": [{"id": "event1"}],
        "pending_meeting": {"duration": 60},
        "awaiting_reschedule_time": True
    }
    
    result = agent._handle_reschedule_time(state)
    assert result is not None
    assert "awaiting_reschedule_time" in result


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_reschedule_no_conflicts(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="Remanejar para 14h")],
        "conflicting_events": [],
        "awaiting_reschedule_time": True
    }
    
    result = agent._handle_reschedule_time(state)
    assert result["awaiting_reschedule_time"] == False
    assert "response" in result


@patch('src.agents.calendar_agent.schedule_meeting')
@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_slot_selection(mock_llm, mock_schedule):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_schedule.return_value = {
        "status": "success",
        "link": "https://calendar.google.com/event/123"
    }
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="1")],
        "pending_meeting": {
            "summary": "Test Meeting",
            "duration_minutes": 60,
            "attendees": []
        },
        "suggested_slots": [
            {"start": "2024-03-20T10:00:00", "end": "2024-03-20T11:00:00"},
            {"start": "2024-03-20T14:00:00", "end": "2024-03-20T15:00:00"}
        ]
    }
    
    result = agent._handle_slot_selection(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_slot_selection_invalid(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="5")],
        "pending_meeting": {"summary": "Test"},
        "suggested_slots": [
            {"start": "2024-03-20T10:00:00", "end": "2024-03-20T11:00:00"}
        ]
    }
    
    result = agent._handle_slot_selection(state)
    assert result is not None
    assert "response" in result


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_slot_selection_no_slots(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="1")],
        "pending_meeting": None,
        "suggested_slots": None
    }
    
    result = agent._handle_slot_selection(state)
    assert result is not None
    assert result["suggested_slots"] is None


@patch('src.agents.calendar_agent.schedule_meeting')
@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_conflict_schedule_anyway(mock_llm, mock_schedule):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_schedule.return_value = {
        "status": "success",
        "link": "https://calendar.google.com/event/123"
    }
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="1")],
        "pending_meeting": {
            "summary": "Test Meeting",
            "start_time": "2024-03-20T10:00:00",
            "duration_minutes": 60
        },
        "conflicting_events": [{"id": "123", "summary": "Existing"}]
    }
    
    result = agent._handle_conflict_resolution(state)
    assert result is not None
    assert result["pending_meeting"] is None


@patch('src.agents.calendar_agent.cancel_meeting')
@patch('src.agents.calendar_agent.schedule_meeting')
@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_conflict_cancel_and_schedule(mock_llm, mock_schedule, mock_cancel):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_cancel.return_value = {"status": "success"}
    mock_schedule.return_value = {"status": "success", "link": "https://calendar.google.com/event/456"}
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="2")],
        "pending_meeting": {
            "summary": "New Meeting",
            "start_time": "2024-03-20T10:00:00",
            "duration_minutes": 60
        },
        "conflicting_events": [{"id": "123", "summary": "Old Meeting"}]
    }
    
    result = agent._handle_conflict_resolution(state)
    assert result is not None
    assert result["pending_meeting"] is None


@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_conflict_reschedule(mock_llm):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="3")],
        "pending_meeting": {
            "summary": "Test Meeting",
            "start_time": "2024-03-20T10:00:00"
        },
        "conflicting_events": [{"id": "123", "summary": "Existing Meeting"}]
    }
    
    result = agent._handle_conflict_resolution(state)
    assert result is not None
    assert result["awaiting_reschedule_time"] == True


@patch('src.agents.calendar_agent.find_available_slots')
@patch('src.agents.calendar_agent.ChatOpenAI')
def test_calendar_agent_handle_conflict_suggest_alternatives(mock_llm, mock_find_slots):
    from src.agents.calendar_agent import CalendarAgent
    from langchain_core.messages import HumanMessage
    
    mock_llm_instance = Mock()
    mock_llm.return_value = mock_llm_instance
    
    mock_find_slots.return_value = {
        "status": "success",
        "slots": [
            {"start": "2024-03-20T14:00:00", "end": "2024-03-20T15:00:00"},
            {"start": "2024-03-20T16:00:00", "end": "2024-03-20T17:00:00"}
        ]
    }
    
    agent = CalendarAgent()
    state = {
        "messages": [HumanMessage(content="4")],
        "pending_meeting": {
            "summary": "Test Meeting",
            "duration_minutes": 60
        },
        "conflicting_events": [{"id": "123", "summary": "Existing", "start": "2024-03-20T10:00:00"}]
    }
    
    result = agent._handle_conflict_resolution(state)
    assert result is not None
