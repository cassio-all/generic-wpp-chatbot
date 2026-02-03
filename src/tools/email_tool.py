"""Email sending tool using SendGrid."""
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from src.config import settings
import structlog

logger = structlog.get_logger()


def send_email(
    to_email: str,
    subject: str,
    content: str,
    from_email: Optional[str] = None
) -> dict:
    """Send an email using SendGrid.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        content: Email content (plain text)
        from_email: Sender email address (optional, uses default from settings)
        
    Returns:
        Dictionary with status and message
    """
    if not settings.sendgrid_api_key:
        logger.warning("SendGrid API key not configured")
        return {
            "status": "error",
            "message": "Email service not configured. Please set SENDGRID_API_KEY."
        }
    
    try:
        message = Mail(
            from_email=from_email or settings.sender_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )
        
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        
        logger.info(
            "Email sent successfully",
            to=to_email,
            subject=subject,
            status_code=response.status_code
        )
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {to_email}",
            "status_code": response.status_code
        }
    except Exception as e:
        logger.error("Error sending email", error=str(e), to=to_email)
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }
