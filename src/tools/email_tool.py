"""Email sending tool using Gmail SMTP."""
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import settings
import structlog
import re

logger = structlog.get_logger()


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def send_email(
    to_email: str,
    subject: str,
    content: str,
    html_content: Optional[str] = None,
    from_email: Optional[str] = None
) -> dict:
    """Send an email using Gmail SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        content: Email content (plain text)
        html_content: Optional HTML version of the email
        from_email: Sender email address (optional, uses Gmail from settings)
        
    Returns:
        Dictionary with status and message
    """
    if not settings.gmail_address or not settings.gmail_app_password:
        logger.warning("Gmail credentials not configured")
        return {
            "status": "error",
            "message": "Email service not configured. Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
        }
    
    # Validate email addresses
    if not validate_email(to_email):
        return {
            "status": "error",
            "message": f"Invalid recipient email address: {to_email}"
        }
    
    sender = from_email or settings.gmail_address
    
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender
        message['To'] = to_email
        
        # Add plain text part
        text_part = MIMEText(content, 'plain', 'utf-8')
        message.attach(text_part)
        
        # Add HTML part if provided
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
        
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.gmail_address, settings.gmail_app_password)
            server.send_message(message)
        
        logger.info(
            "Email sent successfully via Gmail",
            to=to_email,
            subject=subject[:50]
        )
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {to_email}"
        }
    
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail authentication failed")
        return {
            "status": "error",
            "message": "Authentication failed. Check your Gmail App Password."
        }
    except Exception as e:
        logger.error("Error sending email", error=str(e), to=to_email)
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }
