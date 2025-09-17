from typing import List, Dict, Any
from google.adk.tools import ToolContext
from tasky_agent.utils import connect_db, validate_uuid

def delete_tasks(task_ids: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """Deletes multiple tasks from the User's tasks database given their ids.

    Args:
        task_ids (List[str]): A list of task IDs (UUID strings) to delete.

    Returns:
        Dict[str, Any]: Dictionary containing the status of the operation and details.
    """
    if not task_ids:
        return {
            "status": "error",
            "message": "No task IDs provided to delete"
        }

    # Validate all UUIDs first
    for task_id in task_ids:
        if not validate_uuid(task_id):
            return {
                "status": "error",
                "message": f"Invalid UUID format for task_id: {task_id}"
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
        results = {
            "successful_deletes": [],
            "failed_deletes": []
        }
        
        for task_id in task_ids:
            try:
                task = supabase.table("tasks")\
                    .select("*")\
                    .eq("id", task_id)\
                    .eq("user_id", user_id)\
                    .execute()
                    
                if not task.data:
                    results["failed_deletes"].append({
                        "task_id": task_id,
                        "reason": f"Task with ID {task_id} not found or unauthorized"
                    })
                    continue
            except Exception as check_error:
                results["failed_deletes"].append({
                    "task_id": task_id,
                    "reason": f"Database error checking task existence: {str(check_error)}"
                })
                continue
            
            try:
                delete_result = supabase.table("tasks")\
                    .delete()\
                    .eq("id", task_id)\
                    .eq("user_id", user_id)\
                    .execute()
                
                if delete_result.data:
                    results["successful_deletes"].append(task_id)
                else:
                    results["failed_deletes"].append({
                        "task_id": task_id,
                        "reason": "Delete operation returned no data"
                    })
            except Exception as delete_error:
                results["failed_deletes"].append({
                    "task_id": task_id,
                    "reason": f"Database delete error: {str(delete_error)}"
                })
        
        return {
            "status": "success" if results["successful_deletes"] else "error",
            "message": f"Successfully deleted {len(results['successful_deletes'])} task(s), failed to delete {len(results['failed_deletes'])} task(s).",
            "results": results
        }
    
    except Exception as e:
        import logging
        logging.error(f"Exception in delete_tasks: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error deleting tasks: {str(e)}"
        }
