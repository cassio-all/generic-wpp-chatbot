"""Agent integration and automation module."""
from typing import Optional, Dict, Any
import structlog
from datetime import datetime, timedelta
import re

from src.tools import (
    create_task,
    schedule_meeting,
    list_tasks,
    get_upcoming_deadlines
)

logger = structlog.get_logger()


class AgentIntegration:
    """Handles intelligent integration between different agents."""
    
    def __init__(self):
        """Initialize the integration module."""
        pass
    
    def task_to_calendar(self, task_id: int, task_title: str, deadline: str) -> Optional[Dict[str, Any]]:
        """Automatically create calendar event when task has a deadline.
        
        Args:
            task_id: Task ID
            task_title: Task title
            deadline: Deadline in ISO format
            
        Returns:
            Calendar event details or None
        """
        try:
            # Parse deadline
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            
            # Set event 30 minutes before deadline as reminder
            event_time = deadline_dt - timedelta(minutes=30)
            
            # Create calendar event
            result = schedule_meeting(
                summary=f"⏰ Lembrete: {task_title}",
                start_time=event_time.isoformat(),
                duration_minutes=30,
                attendees=[]
            )
            
            if result["status"] == "success":
                logger.info("Task converted to calendar event",
                           task_id=task_id,
                           event_id=result.get("event_id"))
                return result
            
        except Exception as e:
            logger.error("Error converting task to calendar", error=str(e))
        
        return None
    
    def detect_task_creation_intent(self, message: str) -> Optional[Dict[str, str]]:
        """Detect if message is asking to remember something (should create task).
        
        Args:
            message: User message
            
        Returns:
            Task details if intent detected, None otherwise
        """
        # Keywords that indicate "remember to do X"
        remember_patterns = [
            r'lembr[ae]r?\s+(?:de|que|me)?\s*(.+)',
            r'n[ãa]o\s+(?:esquecer|esque[çc]a)\s+(?:de)?\s*(.+)',
            r'preciso\s+(.+)',
            r'tenho\s+que\s+(.+)',
            r'devo\s+(.+)',
        ]
        
        for pattern in remember_patterns:
            match = re.search(pattern, message.lower())
            if match:
                task_content = match.group(1).strip()
                return {
                    "title": task_content,
                    "priority": "medium"
                }
        
        return None
    
    def should_add_calendar_event(self, task_data: Dict[str, Any]) -> bool:
        """Determine if a task should automatically create a calendar event.
        
        Args:
            task_data: Task information
            
        Returns:
            True if should create calendar event
        """
        # Create calendar event if:
        # 1. Task has a deadline
        # 2. Priority is high or urgent
        # 3. Deadline is within next 7 days
        
        if not task_data.get("deadline"):
            return False
        
        priority = task_data.get("priority", "medium")
        if priority not in ["high", "urgent"]:
            return False
        
        try:
            deadline = datetime.fromisoformat(task_data["deadline"].replace('Z', '+00:00'))
            days_until = (deadline - datetime.now()).days
            
            return 0 <= days_until <= 7
            
        except:
            return False
    
    def suggest_follow_up_task(self, email_subject: str, sender: str) -> Dict[str, str]:
        """Suggest creating a follow-up task after reading an important email.
        
        Args:
            email_subject: Email subject
            sender: Email sender
            
        Returns:
            Suggested task data
        """
        return {
            "title": f"Responder email: {email_subject}",
            "description": f"Follow-up de email de {sender}",
            "priority": "medium"
        }
    
    def check_overdue_tasks(self) -> list:
        """Check for overdue tasks and return them.
        
        Returns:
            List of overdue tasks
        """
        try:
            # Get all pending tasks
            result = list_tasks(status="pending")
            
            if result["status"] != "success":
                return []
            
            tasks = result.get("tasks", [])
            overdue = []
            now = datetime.now()
            
            for task in tasks:
                deadline = task.get("deadline")
                if not deadline:
                    continue
                
                try:
                    deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    if deadline_dt < now:
                        overdue.append(task)
                except:
                    continue
            
            return overdue
            
        except Exception as e:
            logger.error("Error checking overdue tasks", error=str(e))
            return []
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Generate daily summary of tasks and events.
        
        Returns:
            Summary with tasks and deadlines
        """
        try:
            # Get pending tasks
            tasks_result = list_tasks(status="pending")
            pending_count = tasks_result.get("count", 0) if tasks_result["status"] == "success" else 0
            
            # Get upcoming deadlines (next 3 days)
            deadlines_result = get_upcoming_deadlines(days=3)
            upcoming_count = deadlines_result.get("count", 0) if deadlines_result["status"] == "success" else 0
            
            # Check overdue
            overdue = self.check_overdue_tasks()
            overdue_count = len(overdue)
            
            return {
                "pending_tasks": pending_count,
                "upcoming_deadlines": upcoming_count,
                "overdue_tasks": overdue_count,
                "overdue": overdue
            }
            
        except Exception as e:
            logger.error("Error generating daily summary", error=str(e))
            return {}
    
    def smart_create_task_with_calendar(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Smart task creation that automatically creates calendar event if needed.
        
        Args:
            title: Task title
            description: Task description
            priority: Task priority
            deadline: Task deadline
            
        Returns:
            Result with task and optional calendar event
        """
        result = {
            "task": None,
            "calendar_event": None,
            "auto_calendar": False
        }
        
        # Create task
        task_result = create_task(
            title=title,
            description=description,
            priority=priority,
            deadline=deadline
        )
        
        if task_result["status"] != "success":
            return result
        
        result["task"] = task_result["task"]
        
        # Check if should create calendar event
        if self.should_add_calendar_event(task_result["task"]):
            calendar_result = self.task_to_calendar(
                task_id=task_result["task"]["id"],
                task_title=title,
                deadline=deadline
            )
            
            if calendar_result:
                result["calendar_event"] = calendar_result
                result["auto_calendar"] = True
                logger.info("Auto-created calendar event for task",
                           task_id=task_result["task"]["id"])
        
        return result
