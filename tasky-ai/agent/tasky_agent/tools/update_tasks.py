import sqlite3
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..config import Config
from ..utils import connect_db, parse_date

class TaskUpdateInput(BaseModel):
    task_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed, archived
    due_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    working_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    duration_mins: Optional[int] = None  # Duration in minutes
    priority: Optional[int] = None  # 1=high, 2=medium, 3=low
    tags: Optional[List[str]] = None  # List of tags

def update_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Updates multiple existing tasks in the User's tasks database given their IDs.
    Always give tasks as a list, even if it's just one task.
    
    Args:
        tasks (List[Dict]): List of tasks to be updated. Each task should have:
            - task_id: ID of the task to update
            - title: New title (optional)
            - description: New description (optional)
            - status: New status (optional: pending, in_progress, completed, archived)
            - due_dt: New due date as string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS" (optional)
            - working_dt: New working date as string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS" (optional)
            - duration_mins: New duration in minutes (optional)
            - priority: New priority level (1=high, 2=medium, 3=low) (optional)
            - tags: List of new tags (optional)
    
    Returns:
        Dict[str, Any]: A dictionary containing the status and message of the operation.
    """
    config = Config().get_config()
    tasks_db_path = config.get("tasks_db_path", ".tasky/dbs/tasks.db")
    
    try:
        # Parse and validate the task inputs
        validated_tasks = []
        for task_data in tasks:
            task = TaskUpdateInput(**task_data)
            validated_tasks.append(task)
            
        conn = connect_db(tasks_db_path)
        cursor = conn.cursor()
        
        results = {
            "successful_updates": [],
            "failed_updates": []
        }
        
        for task in validated_tasks:
            task_dict = task.model_dump()
            task_id = task_dict.pop('task_id')

            # First check if the task exists
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                results["failed_updates"].append({
                    "task_id": task_id,
                    "reason": f"Task with ID {task_id} not found"
                })
                continue
            
            # Prepare the update query
            update_fields = []
            update_values = []

            for key, value in task_dict.items():
                if value is not None:
                    if key in ['due_dt', 'working_dt']:
                        try:
                            value = parse_date(value).isoformat()
                        except ValueError:
                            results["failed_updates"].append({
                                "task_id": task_id,
                                "reason": f"Invalid date format for {key}: {value}. Must be in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format"
                            })
                            continue

                    if key in ['status'] and value not in ['pending', 'in_progress', 'completed', 'archived']:
                        results["failed_updates"].append({
                            "task_id": task_id,
                            "reason": f"Invalid status: {value}. Must be one of: pending, in_progress, completed, archived"
                        })
                        continue

                    if key == 'priority' and value not in [1, 2, 3]:
                        results["failed_updates"].append({
                            "task_id": task_id,
                            "reason": f"Invalid priority: {value}. Must be one of: 1 (high), 2 (medium), 3 (low)"
                        })
                        continue

                    if key == 'tags':
                        value = ','.join(value) if isinstance(value, list) else value

                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            if not update_fields:
                results["failed_updates"].append({
                    "task_id": task_id,
                    "reason": "No fields provided for update"
                })
                continue

            # Execute the update query
            update_query = f"UPDATE tasks SET {', '.join(update_fields)}, updated_at = datetime('now') WHERE id = ?"
            update_values.append(task_id)

            cursor.execute(update_query, update_values)

            if cursor.rowcount > 0:
                results["successful_updates"].append({
                    "task_id": task_id,
                    "message": "Task updated successfully"
                })
            else:
                results["failed_updates"].append({
                    "task_id": task_id,
                    "reason": "No changes made or task not found"
                })
            
        conn.commit()

        return {
            "status": "success",
            "message": f"Updated {len(results['successful_updates'])} tasks successfully, {len(results['failed_updates'])} failed",
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
            "message": f"Error updating tasks: {str(e)}"
        }
    
    finally:
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    # Example usage
    task_input = [
        {
            "task_id": 1,
            "title": "Updated Task Title",
            "status": "in_progress",
            "due_dt": "2023-12-31 23:59:59",
        }
    ]
    
    result = update_tasks(task_input)
    print(result)