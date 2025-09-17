from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from google.adk.tools import ToolContext
from tasky_agent.utils import connect_db, parse_date

class GetTaskInput(BaseModel):
    working_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    due_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    status: Optional[str] = None  # pending, in_progress, completed, archived
    priority: Optional[int] = None  # 1=high, 2=medium, 3=low
    tags: Optional[List[str]] = None  # List of tags to filter by

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
    supabase = connect_db()
    user_id = tool_context._invocation_context.user_id
    
    if filters is None:
        filters = {}
    
    try:
        # Validate and parse the filters
        filter_model = GetTaskInput(**filters)
        validated_filters = {k: v for k, v in filter_model.model_dump().items() if v is not None}
        
        # Start building the Supabase query
        query = supabase.table("tasks").select("*").eq("user_id", user_id)
        
        # Apply filters
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
        
        # Execute the query
        response = query.execute()
        tasks = response.data

        # Format the response
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