import sqlite3
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..config import Config
from ..utils import parse_date, connect_db

class TaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"  # pending, in_progress, completed, archived
    due_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    working_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    duration_mins: Optional[int] = 0  # Duration in minutes
    priority: Optional[int] = 2  # 1=high, 2=medium, 3=low
    tags: Optional[List[str]] = None  # List of tags associated with the task

def create_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inserts one or more tasks in the User's tasks database.
    Always give tasks as a list, even if it's just one task.
    
    Args:
        tasks (List[Dict]): List of tasks to be created. Each task should have:
            - title: Required task title
            - description: Optional task description
            - status: Optional task status (pending, in_progress, completed, archived)
            - due_dt: Optional due date as string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - working_dt: Optional working date as string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - priority: Optional priority level (1=high, 2=medium, 3=low)
            - tags: Optional list of tags associated with the task

    Returns:
        Dict[str, Any]: A dictionary containing the status and message of the operation.
    """
    config = Config().get_config()
    tasks_db_path = config.get("tasks_db_path", ".tasky/dbs/tasks.db")
    
    try:
        # Parse and validate the task inputs
        validated_tasks = []
        for task_data in tasks:
            task = TaskInput(**task_data)
            validated_tasks.append(task)
        
        conn = connect_db(tasks_db_path)
        cursor = conn.cursor()
        
        for task in validated_tasks:
            # Validate the date formats
            due_dt = task.due_dt
            working_dt = task.working_dt
            
            if due_dt:
                try:
                    due_dt = parse_date(due_dt)
                except ValueError:
                    return {"status": "error", "message": f"Invalid deadline date format: {due_dt}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"}
            
            if working_dt:
                try:
                    working_dt = parse_date(working_dt)
                except ValueError:
                    return {"status": "error", "message": f"Invalid working date format: {working_dt}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"}
            
            # Insert the task into the database
            cursor.execute("""
                INSERT INTO tasks (title, description, status, due_dt, working_dt, duration_mins, priority, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.title,
                task.description or '',
                task.status,
                due_dt.isoformat() if due_dt is not None else None,
                working_dt.isoformat() if working_dt is not None else None,
                task.duration_mins,
                task.priority,
                ','.join(task.tags) if task.tags else None
            ))
        
        conn.commit()
        return {
            "status": "success",
            "message": f"Successfully created {len(validated_tasks)} task(s).",
            "task_count": len(validated_tasks)
        }
    
    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating tasks: {str(e)}"
        }
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Example usage
    tasks = [
        {
            "title": "Complete project report",
            "due_dt": "2025-07-15 14:00:00"
        }
    ]
    result = create_tasks(tasks)
    print(result)