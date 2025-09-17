from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from google.adk.tools import ToolContext
from tasky_agent.utils import connect_db, parse_date

class GetTaskInput(BaseModel):
    working_dt: Optional[str] = None
    due_dt: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None

def get_tasks(filters: Optional[Dict[str, Any]], tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieves tasks from the User's tasks database based on provided filters.
    Provide empty dictionary to retrieve all tasks.
    
    Args:
        filters (Dict[str, Any], optional): Dictionary containing filter criteria:
            - working_dt: Date for which tasks are being retrieved
            - due_dt: Due date for the tasks
            - status: Status of the tasks to filter by
            - priority: Priority of the tasks to filter by
            - tags: List of tags to filter tasks by
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - status: "success" or "error"
            - tasks: List of task objects, each containing task_id (UUID) for update/delete operations
            - count: Number of tasks returned
    """
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

    if filters is None:
        filters = {}
    
    try:
        try:
            filter_model = GetTaskInput(**filters)
            validated_filters = {k: v for k, v in filter_model.model_dump().items() if v is not None}
        except Exception as validation_error:
            return {
                "status": "error",
                "message": f"Filter validation error: {str(validation_error)}"
            }
        
        query = supabase.table("tasks").select("*").eq("user_id", user_id)
        
        for key, value in validated_filters.items():
            if key == 'tags':
                for tag in value:
                    query = query.contains('tags', [tag])
                continue

            if key in ['working_dt', 'due_dt']:
                try:
                    parsed_date = parse_date(value)
                    value = parsed_date.isoformat()
                except ValueError:
                    return {
                        "status": "error", 
                        "message": f"Invalid date format for {key}: {value}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    }
            
            query = query.eq(key, value)
        
        try:
            response = query.execute()
            tasks = response.data if response.data else []
        except Exception as query_error:
            return {
                "status": "error",
                "message": f"Database query error: {str(query_error)}"
            }

        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "task_id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "created_at": task["created_at"],
                "updated_at": task.get("updated_at"),
                "due_dt": task["due_dt"],
                "working_dt": task["working_dt"],
                "duration_mins": task["duration_mins"],
                "priority": task["priority"],
                "tags": task["tags"] if task["tags"] else []
            }
            formatted_tasks.append(formatted_task)

        return {
            "status": "success",
            "tasks": formatted_tasks,
            "count": len(formatted_tasks)
        }

    except Exception as e:
        import logging
        logging.error(f"Exception in get_tasks: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error retrieving tasks: {str(e)}"
        }