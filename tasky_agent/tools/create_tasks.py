from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.adk.tools import ToolContext
from tasky_agent.utils import connect_db, parse_date

class TaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"  # pending, in_progress, completed, archived
    due_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    working_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    duration_mins: Optional[int] = 0  # Duration in minutes
    priority: Optional[int] = 2  # 1=high, 2=medium, 3=low
    tags: Optional[List[str]] = None  # List of tags associated with the task

def create_tasks(tasks: List[Dict[str, Any]], tool_context: ToolContext) -> Dict[str, Any]:
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
    supabase = connect_db()
    user_id = tool_context._invocation_context.user_id
    
    try:
        # Parse and validate the task inputs
        validated_tasks = []
        for task_data in tasks:
            task = TaskInput(**task_data)
            validated_tasks.append(task)
        
        errors = []
        created_count = 0

        for idx, task in enumerate(validated_tasks):
            # Validate the date formats
            due_dt = task.due_dt
            working_dt = task.working_dt

            if due_dt:
                try:
                    due_dt = parse_date(due_dt)
                except ValueError:
                    errors.append({
                        "task_index": idx,
                        "title": task.title,
                        "error": f"Invalid deadline date format: {task.due_dt}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    })
                    continue

            if working_dt:
                try:
                    working_dt = parse_date(working_dt)
                except ValueError:
                    errors.append({
                        "task_index": idx,
                        "title": task.title,
                        "error": f"Invalid working date format: {task.working_dt}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    })
                    continue

            # Insert the task into Supabase
            task_data = {
                "user_id": user_id,
                "title": task.title,
                "description": task.description if task.description else None,
                "status": task.status,
                "due_dt": due_dt.isoformat() if due_dt else None,
                "working_dt": working_dt.isoformat() if working_dt else None,
                "duration_mins": task.duration_mins,
                "priority": task.priority,
                "tags": task.tags if task.tags else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            supabase.table("tasks").insert(task_data).execute()
            created_count += 1

        result = {
            "status": "success" if created_count > 0 else "error",
            "message": f"Successfully created {created_count} task(s)." if created_count > 0 else "No tasks created due to errors.",
            "task_count": created_count
        }
        if errors:
            result["errors"] = errors

        return result
    
    except Exception as e:
        import logging
        logging.error(f"Exception in create_tasks: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error creating tasks: {str(e)}"
        }