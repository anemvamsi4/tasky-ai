import sqlite3
from datetime import datetime
from typing import List, Dict, Any

from ..config import Config

def delete_tasks(task_ids: List[int]) -> Dict[str, Any]:
    """Deletes multiple tasks from the User's tasks database given their ids.

    Args:
        task_ids (List[int]): A list of task IDs to delete.

    Returns:
        Dict[str, Any]: Dictionary containing the status of the operation and details of successful and failed deletions.
    """
    config = Config().get_config()
    tasks_db_path = config.get("tasks_db_path", ".tasky/dbs/tasks.db")
    
    try:
        conn = sqlite3.connect(tasks_db_path)
        cursor = conn.cursor()
        
        results = {
            "successful_deletes": [],
            "failed_deletes": []
        }
        
        for task_id in task_ids:
            # Check if the task exists
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                results["failed_deletes"].append({
                    "task_id": task_id,
                    "reason": f"Task with ID {task_id} not found"
                })
                continue
            
            # Delete the task
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
            if cursor.rowcount > 0:
                results["successful_deletes"].append(task_id)
            else:
                results["failed_deletes"].append({
                    "task_id": task_id,
                    "reason": "Failed to delete"
                })
        
        conn.commit()
        
        return {
            "status": "success",
            "message": f"Successfully deleted {len(results['successful_deletes'])} task(s), failed to delete {len(results['failed_deletes'])} task(s).",
            "results": results
        }
    
    except sqlite3.Error as e:
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error deleting tasks: {str(e)}"
        }
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Example usage
    task_ids_to_delete = [1, 2, 3]
    result = delete_tasks(task_ids_to_delete)
    print(result)