from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.adk.tools import ToolContext
from tasky_agent.utils import connect_db, parse_date, validate_uuid

class TaskUpdateInput(BaseModel):
    task_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_dt: Optional[str] = None
    working_dt: Optional[str] = None
    duration_mins: Optional[int] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None

def update_tasks(tasks: List[Dict[str, Any]], tool_context: ToolContext) -> Dict[str, Any]:
    """Updates multiple existing tasks in the User's tasks database given their IDs.
    Always give tasks as a list, even if it's just one task.
    
    Args:
        tasks (List[Dict]): List of tasks to be updated. Each task should have:
            - task_id: Required task ID (UUID string) to update
            - title: Optional task title
            - description: Optional task description
            - status: Optional task status (pending, in_progress, completed, archived)
            - due_dt: Optional due date as string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - working_dt: Optional working date as string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - duration_mins: Optional duration in minutes
            - priority: Optional priority level (1=high, 2=medium, 3=low)
            - tags: Optional list of tags associated with the task
    
    Returns:
        Dict[str, Any]: A dictionary containing the status and message of the operation.
    """
    if not tasks:
        return {
            "status": "error",
            "message": "No tasks provided to update"
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
                task = TaskUpdateInput(**task_data)
                
                # Validate UUID format
                if not validate_uuid(task.task_id):
                    return {
                        "status": "error",
                        "message": f"Invalid UUID format for task_id in task {idx}: {task.task_id}"
                    }
                
                validated_tasks.append(task)
            except Exception as validation_error:
                return {
                    "status": "error",
                    "message": f"Validation error for task {idx}: {str(validation_error)}"
                }
            
        results = {
            "successful_updates": [],
            "failed_updates": []
        }
        
        for task in validated_tasks:
            task_dict = task.model_dump()
            task_id = task_dict.pop('task_id')

            # First check if the task exists and belongs to the user
            try:
                response = supabase.table("tasks").select("*").eq("id", task_id).eq("user_id", user_id).execute()
                if not response.data:
                    results["failed_updates"].append({
                        "task_id": task_id,
                        "reason": f"Task with ID {task_id} not found or not owned by user"
                    })
                    continue
            except Exception as db_error:
                results["failed_updates"].append({
                    "task_id": task_id,
                    "reason": f"Database error checking task existence: {str(db_error)}"
                })
                continue
            
            update_data = {}
            
            for key, value in task_dict.items():
                if value is not None:
                    if key in ['due_dt', 'working_dt']:
                        try:
                            value = parse_date(value).isoformat()
                        except ValueError:
                            results["failed_updates"].append({
                                "task_id": task_id,
                                "reason": f"Invalid date format for {key}: {value}"
                            })
                            continue

                    if key == 'status' and value not in ['pending', 'in_progress', 'completed', 'archived']:
                        results["failed_updates"].append({
                            "task_id": task_id,
                            "reason": f"Invalid status: {value}"
                        })
                        continue

                    if key == 'priority' and value not in [1, 2, 3]:
                        results["failed_updates"].append({
                            "task_id": task_id,
                            "reason": f"Invalid priority: {value}"
                        })
                        continue

                    update_data[key] = value

            if not update_data:
                results["failed_updates"].append({
                    "task_id": task_id,
                    "reason": "No fields provided for update"
                })
                continue

            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            try:
                response = supabase.table("tasks")\
                    .update(update_data)\
                    .eq("id", task_id)\
                    .eq("user_id", user_id)\
                    .execute()

                if response.data:
                    results["successful_updates"].append({
                        "task_id": task_id,
                        "message": "Task updated successfully"
                    })
                else:
                    results["failed_updates"].append({
                        "task_id": task_id,
                        "reason": "Update operation returned no data"
                    })
            except Exception as update_error:
                results["failed_updates"].append({
                    "task_id": task_id,
                    "reason": f"Database update error: {str(update_error)}"
                })

        return {
            "status": "success",
            "message": f"Updated {len(results['successful_updates'])} tasks successfully, {len(results['failed_updates'])} failed",
            "results": results
        }
    
    except Exception as e:
        import logging
        logging.error(f"Exception in update_tasks: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error updating tasks: {str(e)}"
        }
