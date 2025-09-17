from pydantic import BaseModel, validator
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.adk.tools import ToolContext
from tasky_agent.utils import connect_db, parse_date

class TaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "pending"
    due_dt: Optional[str] = None
    working_dt: Optional[str] = None
    duration_mins: Optional[int] = 0
    priority: Optional[int] = 2
    tags: Optional[List[str]] = None

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v.strip()) > 255:
            raise ValueError('Title cannot exceed 255 characters')
        return v.strip()

    @validator('status')
    def status_must_be_valid(cls, v):
        if v and v not in ['pending', 'in_progress', 'completed', 'archived']:
            raise ValueError('Status must be one of: pending, in_progress, completed, archived')
        return v

    @validator('priority')
    def priority_must_be_valid(cls, v):
        if v is not None and v not in [1, 2, 3]:
            raise ValueError('Priority must be 1 (high), 2 (medium), or 3 (low)')
        return v

    @validator('duration_mins')
    def duration_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('Duration must be non-negative')
        return v

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
    if not tasks:
        return {
            "status": "error",
            "message": "No tasks provided to create"
        }

    try:
        supabase = connect_db()
        user_id = tool_context._invocation_context.user_id
        
        if not user_id:
            return {
                "status": "error",
                "message": "User ID not found in context"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }
    
    try:
        validated_tasks = []
        for idx, task_data in enumerate(tasks):
            try:
                task = TaskInput(**task_data)
                validated_tasks.append((idx, task))
            except Exception as validation_error:
                return {
                    "status": "error",
                    "message": f"Validation error for task {idx}: {str(validation_error)}"
                }
        
        errors = []
        created_count = 0

        for idx, task in validated_tasks:
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

            try:
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

                response = supabase.table("tasks").insert(task_data).execute()
                
                if not response.data:
                    errors.append({
                        "task_index": idx,
                        "title": task.title,
                        "error": "Failed to insert task into database"
                    })
                    continue
                    
                created_count += 1
                
            except Exception as db_error:
                errors.append({
                    "task_index": idx,
                    "title": task.title,
                    "error": f"Database error: {str(db_error)}"
                })
                continue

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