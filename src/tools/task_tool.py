"""Task management tool for TODO lists."""
import sqlite3
import structlog
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = structlog.get_logger()

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "tasks.db"


def _init_db():
    """Initialize tasks database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            deadline TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            user_id TEXT DEFAULT 'default'
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Tasks database initialized", db_path=str(DB_PATH))


def create_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    deadline: Optional[str] = None,
    user_id: str = "default"
) -> dict:
    """Create a new task.
    
    Args:
        title: Task title
        description: Optional task description
        priority: Priority level (low, medium, high, urgent)
        deadline: Optional deadline in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        user_id: User identifier
        
    Returns:
        Dictionary with status and task info
    """
    try:
        _init_db()
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority.lower() not in valid_priorities:
            priority = "medium"
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tasks (title, description, priority, status, deadline, created_at, user_id)
            VALUES (?, ?, ?, 'pending', ?, ?, ?)
        """, (title, description, priority.lower(), deadline, created_at, user_id))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info("Task created", task_id=task_id, title=title, priority=priority)
        
        return {
            "status": "success",
            "task": {
                "id": task_id,
                "title": title,
                "description": description,
                "priority": priority.lower(),
                "status": "pending",
                "deadline": deadline,
                "created_at": created_at
            }
        }
        
    except Exception as e:
        logger.error("Error creating task", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to create task: {str(e)}"
        }


def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    user_id: str = "default"
) -> dict:
    """List tasks with optional filtering.
    
    Args:
        status: Filter by status (pending, completed, all)
        priority: Filter by priority (low, medium, high, urgent)
        user_id: User identifier
        
    Returns:
        Dictionary with status and list of tasks
    """
    try:
        _init_db()
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        query = "SELECT id, title, description, priority, status, deadline, created_at, completed_at FROM tasks WHERE user_id = ?"
        params = [user_id]
        
        if status and status.lower() != "all":
            query += " AND status = ?"
            params.append(status.lower())
        
        if priority:
            query += " AND priority = ?"
            params.append(priority.lower())
        
        query += " ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "status": row[4],
                "deadline": row[5],
                "created_at": row[6],
                "completed_at": row[7]
            })
        
        logger.info("Tasks listed", count=len(tasks), status=status, priority=priority)
        
        return {
            "status": "success",
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error("Error listing tasks", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to list tasks: {str(e)}"
        }


def complete_task(task_id: int, user_id: str = "default") -> dict:
    """Mark a task as completed.
    
    Args:
        task_id: Task ID
        user_id: User identifier
        
    Returns:
        Dictionary with status
    """
    try:
        _init_db()
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        completed_at = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE tasks
            SET status = 'completed', completed_at = ?
            WHERE id = ? AND user_id = ?
        """, (completed_at, task_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return {
                "status": "error",
                "message": f"Task {task_id} not found"
            }
        
        conn.commit()
        conn.close()
        
        logger.info("Task completed", task_id=task_id)
        
        return {
            "status": "success",
            "message": f"Task {task_id} marked as completed",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error("Error completing task", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to complete task: {str(e)}"
        }


def delete_task(task_id: int, user_id: str = "default") -> dict:
    """Delete a task.
    
    Args:
        task_id: Task ID
        user_id: User identifier
        
    Returns:
        Dictionary with status
    """
    try:
        _init_db()
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return {
                "status": "error",
                "message": f"Task {task_id} not found"
            }
        
        conn.commit()
        conn.close()
        
        logger.info("Task deleted", task_id=task_id)
        
        return {
            "status": "success",
            "message": f"Task {task_id} deleted",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error("Error deleting task", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to delete task: {str(e)}"
        }


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    deadline: Optional[str] = None,
    user_id: str = "default"
) -> dict:
    """Update a task.
    
    Args:
        task_id: Task ID
        title: New title
        description: New description
        priority: New priority
        deadline: New deadline
        user_id: User identifier
        
    Returns:
        Dictionary with status
    """
    try:
        _init_db()
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Build update query dynamically
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:  # Allow empty string
            updates.append("description = ?")
            params.append(description)
        
        if priority:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if priority.lower() in valid_priorities:
                updates.append("priority = ?")
                params.append(priority.lower())
        
        if deadline is not None:  # Allow None to remove deadline
            updates.append("deadline = ?")
            params.append(deadline)
        
        if not updates:
            conn.close()
            return {
                "status": "error",
                "message": "No fields to update"
            }
        
        params.extend([task_id, user_id])
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            conn.close()
            return {
                "status": "error",
                "message": f"Task {task_id} not found"
            }
        
        conn.commit()
        conn.close()
        
        logger.info("Task updated", task_id=task_id)
        
        return {
            "status": "success",
            "message": f"Task {task_id} updated",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error("Error updating task", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to update task: {str(e)}"
        }


def get_upcoming_deadlines(days: int = 7, user_id: str = "default") -> dict:
    """Get tasks with upcoming deadlines.
    
    Args:
        days: Number of days to look ahead
        user_id: User identifier
        
    Returns:
        Dictionary with status and tasks
    """
    try:
        _init_db()
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = datetime.now()
        future = datetime.now().replace(hour=23, minute=59, second=59)
        from datetime import timedelta
        future = (now + timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT id, title, description, priority, status, deadline, created_at
            FROM tasks
            WHERE user_id = ? AND status = 'pending' AND deadline IS NOT NULL AND deadline <= ?
            ORDER BY deadline ASC
        """, (user_id, future))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "status": row[4],
                "deadline": row[5],
                "created_at": row[6]
            })
        
        logger.info("Upcoming deadlines retrieved", count=len(tasks), days=days)
        
        return {
            "status": "success",
            "tasks": tasks,
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error("Error getting upcoming deadlines", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to get upcoming deadlines: {str(e)}"
        }
