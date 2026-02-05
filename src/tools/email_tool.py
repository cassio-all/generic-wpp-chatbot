"""Email tool using Gmail SMTP and IMAP."""
from typing import Optional, List
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timedelta
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
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    from_email: Optional[str] = None
) -> dict:
    """Send an email using Gmail SMTP.
    
    Args:
        to_email: Recipient email address (can be comma-separated)
        subject: Email subject
        content: Email content (plain text)
        html_content: Optional HTML version of the email
        cc: List of CC recipients
        bcc: List of BCC recipients
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
        
        if cc:
            message['Cc'] = ', '.join(cc)
        if bcc:
            message['Bcc'] = ', '.join(bcc)
        
        # Add plain text part
        text_part = MIMEText(content, 'plain', 'utf-8')
        message.attach(text_part)
        
        # Add HTML part if provided
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
        
        # Build recipient list
        all_recipients = [to_email]
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)
        
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.gmail_address, settings.gmail_app_password)
            server.send_message(message, to_addrs=all_recipients)
        
        logger.info(
            "Email sent successfully via Gmail",
            to=to_email,
            subject=subject[:50],
            cc_count=len(cc) if cc else 0,
            bcc_count=len(bcc) if bcc else 0
        )
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {to_email}" + 
                      (f" (+ {len(cc)} CC)" if cc else "") +
                      (f" (+ {len(bcc)} BCC)" if bcc else "")
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


def read_emails(
    max_emails: int = 10,
    folder: str = "INBOX",
    unread_only: bool = False
) -> dict:
    """Read emails from Gmail using IMAP.
    
    Args:
        max_emails: Maximum number of emails to retrieve
        folder: Email folder to read from (default: INBOX)
        unread_only: Only retrieve unread emails
        
    Returns:
        Dictionary with status and list of emails
    """
    if not settings.gmail_address or not settings.gmail_app_password:
        logger.warning("Gmail credentials not configured")
        return {
            "status": "error",
            "message": "Email service not configured",
            "emails": []
        }
    
    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(settings.gmail_address, settings.gmail_app_password)
        mail.select(folder)
        
        # Search for emails
        search_criteria = 'UNSEEN' if unread_only else 'ALL'
        status, messages = mail.search(None, search_criteria)
        
        if status != 'OK':
            return {
                "status": "error",
                "message": "Failed to search emails",
                "emails": []
            }
        
        email_ids = messages[0].split()
        email_ids = email_ids[-max_emails:]  # Get last N emails
        
        emails = []
        for email_id in reversed(email_ids):  # Newest first
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject = ""
                if msg['Subject']:
                    decoded = decode_header(msg['Subject'])[0]
                    if isinstance(decoded[0], bytes):
                        subject = decoded[0].decode(decoded[1] or 'utf-8')
                    else:
                        subject = decoded[0]
                
                # Get email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except:
                                pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        body = str(msg.get_payload())
                
                emails.append({
                    "id": email_id.decode(),
                    "from": msg.get('From', ''),
                    "to": msg.get('To', ''),
                    "subject": subject,
                    "date": msg.get('Date', ''),
                    "body": body[:500]  # Limit body to 500 chars
                })
            except Exception as e:
                logger.error(f"Error parsing email {email_id}", error=str(e))
                continue
        
        mail.close()
        mail.logout()
        
        logger.info(f"Retrieved {len(emails)} emails from {folder}")
        
        return {
            "status": "success",
            "message": f"Retrieved {len(emails)} emails",
            "emails": emails
        }
    
    except Exception as e:
        logger.error("Error reading emails", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to read emails: {str(e)}",
            "emails": []
        }


def search_emails(
    query: str,
    max_emails: int = 10,
    days_back: int = 7
) -> dict:
    """Search emails by subject, sender, or content.
    
    Args:
        query: Search query
        max_emails: Maximum number of results
        days_back: How many days back to search
        
    Returns:
        Dictionary with status and matching emails
    """
    if not settings.gmail_address or not settings.gmail_app_password:
        return {
            "status": "error",
            "message": "Email service not configured",
            "emails": []
        }
    
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(settings.gmail_address, settings.gmail_app_password)
        mail.select('INBOX')
        
        # Search by subject or from
        search_criteria = f'(OR SUBJECT "{query}" FROM "{query}")'
        status, messages = mail.search(None, search_criteria)
        
        if status != 'OK':
            return {
                "status": "error",
                "message": "Search failed",
                "emails": []
            }
        
        email_ids = messages[0].split()[-max_emails:]
        
        emails = []
        for email_id in reversed(email_ids):
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = ""
                if msg['Subject']:
                    decoded = decode_header(msg['Subject'])[0]
                    if isinstance(decoded[0], bytes):
                        subject = decoded[0].decode(decoded[1] or 'utf-8')
                    else:
                        subject = decoded[0]
                
                emails.append({
                    "id": email_id.decode(),
                    "from": msg.get('From', ''),
                    "subject": subject,
                    "date": msg.get('Date', '')
                })
            except Exception as e:
                logger.error(f"Error parsing email {email_id}", error=str(e))
                continue
        
        mail.close()
        mail.logout()
        
        logger.info(f"Found {len(emails)} emails matching '{query}'")
        
        return {
            "status": "success",
            "message": f"Found {len(emails)} matching emails",
            "emails": emails
        }
    
    except Exception as e:
        logger.error("Error searching emails", error=str(e))
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "emails": []
        }
