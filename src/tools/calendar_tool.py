"""Google Calendar integration for scheduling meetings."""
import os
import datetime
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.config import settings
import structlog

logger = structlog.get_logger()

# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    """Get authenticated Google Calendar service."""
    creds = None
    
    # Check if token file exists
    if os.path.exists(settings.google_calendar_token_path):
        creds = Credentials.from_authorized_user_file(
            settings.google_calendar_token_path,
            SCOPES
        )
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(settings.google_calendar_credentials_path):
                logger.warning("Google Calendar credentials not found")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.google_calendar_credentials_path,
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(settings.google_calendar_token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)


def schedule_meeting(
    summary: str,
    start_time: str,
    duration_minutes: int = 60,
    attendees: Optional[list] = None,
    description: Optional[str] = None
) -> dict:
    """Schedule a meeting on Google Calendar.
    
    Args:
        summary: Meeting title/summary
        start_time: Start time in ISO format (e.g., "2024-03-20T10:00:00")
        duration_minutes: Meeting duration in minutes
        attendees: List of attendee email addresses
        description: Meeting description
        
    Returns:
        Dictionary with status and meeting details
    """
    try:
        service = get_calendar_service()
        
        if not service:
            return {
                "status": "error",
                "message": "Google Calendar not configured. Please add credentials."
            }
        
        # Parse start time
        start_dt = datetime.datetime.fromisoformat(start_time)
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
        
        # Create event
        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Insert event
        event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()
        
        logger.info("Meeting scheduled successfully", event_id=event.get('id'))
        
        return {
            "status": "success",
            "message": "Meeting scheduled successfully",
            "event_id": event.get('id'),
            "link": event.get('htmlLink')
        }
        
    except Exception as e:
        logger.error("Error scheduling meeting", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to schedule meeting: {str(e)}"
        }


def list_upcoming_events(max_results: int = 10) -> dict:
    """List upcoming events from Google Calendar.
    
    Args:
        max_results: Maximum number of events to return
        
    Returns:
        Dictionary with status and list of events
    """
    try:
        service = get_calendar_service()
        
        if not service:
            return {
                "status": "error",
                "message": "Google Calendar not configured"
            }
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({
                'summary': event.get('summary'),
                'start': start,
                'id': event.get('id')
            })
        
        logger.info("Retrieved upcoming events", count=len(event_list))
        
        return {
            "status": "success",
            "events": event_list
        }
        
    except Exception as e:
        logger.error("Error listing events", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to list events: {str(e)}"
        }
