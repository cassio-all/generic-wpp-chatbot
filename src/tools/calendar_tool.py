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
        
        # Parse start time (assume it's in local timezone)
        start_dt = datetime.datetime.fromisoformat(start_time)
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
        
        # Use local timezone instead of UTC
        # This ensures the time shown in Google Calendar matches what the user requested
        local_timezone = 'America/Sao_Paulo'  # Brazilian timezone (UTC-3)
        
        # Create event
        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': local_timezone,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': local_timezone,
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


def check_conflicts(start_time: str, end_time: str) -> dict:
    """Check if there are conflicts in the specified time range.
    
    Args:
        start_time: Start time in ISO format
        end_time: End time in ISO format
        
    Returns:
        Dictionary with conflict status and conflicting events
    """
    try:
        service = get_calendar_service()
        
        if not service:
            return {"status": "error", "message": "Google Calendar not configured"}
        
        # Parse the requested time range
        start_dt = datetime.datetime.fromisoformat(start_time)
        end_dt = datetime.datetime.fromisoformat(end_time)
        
        # Search for events on the entire day to catch all potential conflicts
        day_start = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Format with 'Z' suffix for UTC (Google Calendar API requirement)
        day_start_rfc = day_start.isoformat() + 'Z'
        day_end_rfc = day_end.isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=day_start_rfc,
            timeMax=day_end_rfc,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        all_events = events_result.get('items', [])
        
        # Remove duplicates by event ID and summary+time combination
        seen = set()
        unique_events = []
        for event in all_events:
            event_id = event.get('id')
            summary = event.get('summary', '')
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            
            # Create unique key: use ID if available, otherwise summary+time
            unique_key = event_id if event_id else f"{summary}_{start_time}"
            
            if unique_key not in seen:
                seen.add(unique_key)
                unique_events.append(event)
                logger.debug("Event added", id=event_id, summary=summary, start=start_time)
            else:
                logger.debug("Duplicate event skipped", id=event_id, summary=summary)
        
        logger.info("Events fetched for conflict check", total=len(all_events), unique=len(unique_events))
        
        # Manually check for overlaps
        conflicts = []
        for event in unique_events:
            event_start_str = event['start'].get('dateTime', event['start'].get('date'))
            event_end_str = event['end'].get('dateTime', event['end'].get('date'))
            
            # Skip all-day events
            if 'T' not in event_start_str:
                continue
            
            # Parse event times - extract just YYYY-MM-DDTHH:MM:SS (first 19 chars)
            # Remove timezone info: 2026-02-03T19:00:00-03:00 -> 2026-02-03T19:00:00
            import re
            event_start_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', event_start_str)
            event_end_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', event_end_str)
            
            if not event_start_match or not event_end_match:
                continue
                
            event_start = datetime.datetime.fromisoformat(event_start_match.group(1))
            event_end = datetime.datetime.fromisoformat(event_end_match.group(1))
            
            # Check if there's an overlap
            # Two events overlap if: event_start < requested_end AND event_end > requested_start
            if event_start < end_dt and event_end > start_dt:
                conflicts.append({
                    'id': event.get('id'),
                    'summary': event.get('summary'),
                    'start': event_start_str,
                    'end': event_end_str
                })
        
        if conflicts:
            logger.info("Conflicts detected", count=len(conflicts))
            return {
                "status": "conflict",
                "has_conflict": True,
                "conflicts": conflicts
            }
        
        logger.info("No conflicts found")
        return {
            "status": "success",
            "has_conflict": False,
            "conflicts": []
        }
        
    except Exception as e:
        logger.error("Error checking conflicts", error=str(e))
        return {"status": "error", "message": str(e), "has_conflict": False}


def find_available_slots(date: str, duration_minutes: int = 60, num_suggestions: int = 3) -> dict:
    """Find available time slots on a given date.
    
    Args:
        date: Date in YYYY-MM-DD format
        duration_minutes: Required duration in minutes
        num_suggestions: Number of suggestions to return
        
    Returns:
        Dictionary with available slots
    """
    try:
        service = get_calendar_service()
        
        if not service:
            return {"status": "error", "message": "Google Calendar not configured"}
        
        # Define business hours (8:00 to 22:00)
        start_hour, end_hour = 8, 22
        date_obj = datetime.datetime.fromisoformat(date)
        
        # If it's today, start from current time (rounded up to next hour)
        now = datetime.datetime.now()
        if date_obj.date() == now.date():
            current_hour = now.hour + (1 if now.minute > 0 else 0)
            start_hour = max(start_hour, current_hour)
        
        # Get all events for the day
        day_start = date_obj.replace(hour=start_hour, minute=0, second=0)
        day_end = date_obj.replace(hour=end_hour, minute=0, second=0)
        
        # Format with 'Z' suffix for Google Calendar API
        day_start_rfc = day_start.isoformat() + 'Z'
        day_end_rfc = day_end.isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=day_start_rfc,
            timeMax=day_end_rfc,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Build list of busy periods (remove timezone for comparison)
        busy_periods = []
        import re
        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            end_str = event['end'].get('dateTime', event['end'].get('date'))
            
            # Extract just the datetime part without timezone
            start_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', start_str)
            end_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', end_str)
            
            if start_match and end_match:
                start = datetime.datetime.fromisoformat(start_match.group(1))
                end = datetime.datetime.fromisoformat(end_match.group(1))
                busy_periods.append((start, end))
        
        # Find free slots
        available_slots = []
        current_time = day_start
        duration = datetime.timedelta(minutes=duration_minutes)
        
        while current_time + duration <= day_end and len(available_slots) < num_suggestions:
            slot_end = current_time + duration
            
            # Check if slot is free
            is_free = True
            for busy_start, busy_end in busy_periods:
                if not (slot_end <= busy_start or current_time >= busy_end):
                    is_free = False
                    current_time = busy_end  # Jump to end of busy period
                    break
            
            if is_free:
                available_slots.append({
                    'start': current_time.isoformat(),
                    'end': slot_end.isoformat()
                })
                current_time += datetime.timedelta(hours=1)  # Move to next hour
            
        return {
            "status": "success",
            "available_slots": available_slots
        }
        
    except Exception as e:
        logger.error("Error finding available slots", error=str(e))
        return {"status": "error", "message": str(e)}


def cancel_meeting(event_id: str) -> dict:
    """Cancel a meeting on Google Calendar.
    
    Args:
        event_id: ID of the event to cancel
        
    Returns:
        Dictionary with status
    """
    try:
        service = get_calendar_service()
        
        if not service:
            return {"status": "error", "message": "Google Calendar not configured"}
        
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        logger.info("Meeting cancelled successfully", event_id=event_id)
        
        return {
            "status": "success",
            "message": "Meeting cancelled successfully"
        }
        
    except Exception as e:
        logger.error("Error cancelling meeting", error=str(e))
        return {"status": "error", "message": str(e)}


def update_meeting(event_id: str, new_start_time: str, duration_minutes: int) -> dict:
    """Update meeting time on Google Calendar.
    
    Args:
        event_id: ID of the event to update
        new_start_time: New start time in ISO format
        duration_minutes: Meeting duration in minutes
        
    Returns:
        Dictionary with status
    """
    try:
        service = get_calendar_service()
        
        if not service:
            return {"status": "error", "message": "Google Calendar not configured"}
        
        # Get existing event
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Update times
        start_dt = datetime.datetime.fromisoformat(new_start_time)
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
        local_timezone = 'America/Sao_Paulo'
        
        event['start'] = {
            'dateTime': start_dt.isoformat(),
            'timeZone': local_timezone
        }
        event['end'] = {
            'dateTime': end_dt.isoformat(),
            'timeZone': local_timezone
        }
        
        # Update event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        logger.info("Meeting updated successfully", event_id=event_id)
        
        return {
            "status": "success",
            "message": "Meeting updated successfully",
            "link": updated_event.get('htmlLink')
        }
        
    except Exception as e:
        logger.error("Error updating meeting", error=str(e))
        return {"status": "error", "message": str(e)}


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
