"""Testes para src/tools/calendar_tool.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_schedule_meeting(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import schedule_meeting
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().insert().execute.return_value = {'id': '1', 'htmlLink': 'http://test'}
    mock_build.return_value = mock_service
    result = schedule_meeting("Test", "2024-03-20T10:00:00", 60)
    assert result is not None


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_list_upcoming_events(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import list_upcoming_events
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().list().execute.return_value = {'items': []}
    mock_build.return_value = mock_service
    result = list_upcoming_events(10)
    assert result is not None


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_cancel_meeting(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import cancel_meeting
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().delete().execute.return_value = {}
    mock_build.return_value = mock_service
    result = cancel_meeting("event123")
    assert result is not None


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_update_meeting(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import update_meeting
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().get().execute.return_value = {
        'id': '1', 'summary': 'Old', 'start': {'dateTime': '2024-03-20T10:00:00'},
        'end': {'dateTime': '2024-03-20T11:00:00'}
    }
    mock_service.events().update().execute.return_value = {'id': '1'}
    mock_build.return_value = mock_service
    result = update_meeting("event123", "2024-03-21T14:00:00", 90)
    assert result is not None


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_check_conflicts(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import check_conflicts
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().list().execute.return_value = {'items': []}
    mock_build.return_value = mock_service
    result = check_conflicts("2024-03-20T10:00:00", "2024-03-20T11:00:00")
    assert result is not None


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_get_event_details(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import get_event_details
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().get().execute.return_value = {'id': '1', 'summary': 'Test'}
    mock_build.return_value = mock_service
    result = get_event_details("event123")
    assert result is not None


@patch('src.tools.calendar_tool.build')
@patch('src.tools.calendar_tool.Credentials.from_authorized_user_file')
@patch('src.tools.calendar_tool.os.path.exists')
def test_find_available_slots(mock_exists, mock_creds, mock_build):
    from src.tools.calendar_tool import find_available_slots
    mock_exists.return_value = True
    mock_creds_obj = Mock()
    mock_creds_obj.valid = True
    mock_creds.return_value = mock_creds_obj
    mock_service = Mock()
    mock_service.events().list().execute.return_value = {'items': []}
    mock_build.return_value = mock_service
    result = find_available_slots("2024-03-20", 60)
    assert result is not None
