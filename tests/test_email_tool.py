"""Testes para src/tools/email_tool.py"""
import pytest
from unittest.mock import Mock, patch


@patch('src.tools.email_tool.smtplib.SMTP')
@patch('src.tools.email_tool.settings')
def test_send_email(mock_settings, mock_smtp):
    from src.tools.email_tool import send_email
    mock_settings.gmail_address = "test@gmail.com"
    mock_settings.gmail_app_password = "password"
    mock_server = Mock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    result = send_email("to@test.com", "Subject", "Content")
    assert result is not None


@patch('src.tools.email_tool.imaplib.IMAP4_SSL')
@patch('src.tools.email_tool.settings')
def test_read_emails(mock_settings, mock_imap):
    from src.tools.email_tool import read_emails
    mock_settings.gmail_address = "test@gmail.com"
    mock_settings.gmail_app_password = "password"
    mock_mail = Mock()
    mock_mail.search.return_value = ('OK', [b'1'])
    mock_mail.fetch.return_value = ('OK', [(b'1', {b'RFC822': b'Subject: Test\r\n\r\nBody'})])
    mock_imap.return_value.__enter__.return_value = mock_mail
    result = read_emails(5)
    assert result is not None


@patch('src.tools.email_tool.imaplib.IMAP4_SSL')
@patch('src.tools.email_tool.settings')
def test_search_emails(mock_settings, mock_imap):
    from src.tools.email_tool import search_emails
    mock_settings.gmail_address = "test@gmail.com"
    mock_settings.gmail_app_password = "password"
    mock_mail = Mock()
    mock_mail.search.return_value = ('OK', [b'1'])
    mock_mail.fetch.return_value = ('OK', [(b'1', {b'RFC822': b'Subject: Test\r\n\r\nBody'})])
    mock_imap.return_value.__enter__.return_value = mock_mail
    result = search_emails("test")
    assert result is not None
