"""Testes para src/tools/task_tool.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.tools.task_tool.sqlite3.connect')
def test_create_task(mock_connect):
    from src.tools.task_tool import create_task
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.lastrowid = 1
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    result = create_task("Test Task", "Description", "high")
    assert result is not None


@patch('src.tools.task_tool.sqlite3.connect')
def test_list_tasks(mock_connect):
    from src.tools.task_tool import list_tasks
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [(1, "Task 1", "Desc", "high", "pending", None, "2024-01-01", None, "default")]
    mock_cursor.description = [("id",), ("title",), ("description",), ("priority",), ("status",), ("deadline",), ("created_at",), ("completed_at",), ("user_id",)]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    result = list_tasks()
    assert result is not None


@patch('src.tools.task_tool.sqlite3.connect')
def test_complete_task(mock_connect):
    from src.tools.task_tool import complete_task
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.rowcount = 1
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    result = complete_task(1)
    assert result is not None


@patch('src.tools.task_tool.sqlite3.connect')
def test_delete_task(mock_connect):
    from src.tools.task_tool import delete_task
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.rowcount = 1
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    result = delete_task(1)
    assert result is not None


@patch('src.tools.task_tool.sqlite3.connect')
def test_update_task(mock_connect):
    from src.tools.task_tool import update_task
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.rowcount = 1
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    result = update_task(1, title="Updated Task")
    assert result is not None


@patch('src.tools.task_tool.sqlite3.connect')
def test_list_tasks_with_filters(mock_connect):
    from src.tools.task_tool import list_tasks
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = [("id",), ("title",), ("description",), ("priority",), ("status",), ("deadline",), ("created_at",), ("completed_at",), ("user_id",)]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    result = list_tasks(status="completed", priority="high")
    assert result is not None
