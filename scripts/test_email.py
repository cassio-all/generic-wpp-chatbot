#!/usr/bin/env python3
"""Test script for Gmail email sending."""

import sys
sys.path.insert(0, '.')

from src.tools.email_tool import send_email
from src.config import settings
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

def test_email():
    """Test email sending functionality."""
    
    print("=" * 60)
    print("Gmail Email Sending Test")
    print("=" * 60)
    print()
    
    # Check configuration
    if not settings.gmail_address:
        print("❌ GMAIL_ADDRESS not configured in .env")
        print("   Add: GMAIL_ADDRESS=your_email@gmail.com")
        return False
    
    if not settings.gmail_app_password:
        print("❌ GMAIL_APP_PASSWORD not configured in .env")
        print("   Get it from: https://myaccount.google.com/apppasswords")
        return False
    
    print(f"✅ Gmail configured: {settings.gmail_address}")
    print()
    
    # Get recipient email
    to_email = input("📧 Enter recipient email (or press Enter to use sender): ").strip()
    if not to_email:
        to_email = settings.gmail_address
        print(f"   Using: {to_email} (self-test)")
    print()
    
    # Send test email
    print("📤 Sending test email...")
    
    result = send_email(
        to_email=to_email,
        subject="🤖 Test from WhatsApp Chatbot",
        content="Hello! This is a test email from your WhatsApp Chatbot.\n\nIf you received this, email sending is working correctly! ✅",
        html_content="""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #25D366;">🤖 Test from WhatsApp Chatbot</h2>
                <p>Hello! This is a test email from your WhatsApp Chatbot.</p>
                <p>If you received this, email sending is working correctly! ✅</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sent via Gmail SMTP
                </p>
            </body>
        </html>
        """
    )
    
    print()
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print()
        print("Check your inbox to confirm!")
        return True
    else:
        print(f"❌ {result['message']}")
        return False

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)
