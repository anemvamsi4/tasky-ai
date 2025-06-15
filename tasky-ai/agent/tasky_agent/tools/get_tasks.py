import sqlite3
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..config import Config
from ..utils import parse_date, connect_db

class GetTaskInput(BaseModel):
    working_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    due_dt: Optional[str] = None  # Format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
    status: Optional[str] = None  # pending, in_progress, completed, archived
    priority: Optional[int] = None  # 1=high, 2=medium, 3=low
    tags: Optional[List[str]] = None  # List of tags to filter by

def get_tasks(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieves tasks from the User's tasks database based on provided filters.
    Provide empty dictionary to retrieve all tasks.
    
    Args:
        filters (Dict[str, Any], optional): Dictionary containing filter criteria:
            - working_dt: Date for which tasks are being retrieved in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - due_dt: Due date for the tasks in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - status: Status of the tasks to filter by (pending, in_progress, completed, archived)
            - priority: Priority of the tasks to filter by (1=high, 2=medium, 3=low)
            - tags: List of tags to filter tasks by
    
    Returns:
        Dict[str, Any]: Dictionary containing the status and list of tasks.
    """
    config = Config().get_config()
    tasks_db_path = config.get("tasks_db_path", ".tasky/dbs/tasks.db")
    
    
    if filters is None:
        filters = {}
    
    try:
        # Validate and parse the filters
        filter_model = GetTaskInput(**filters)
        validated_filters = {k: v for k, v in filter_model.model_dump().items() if v is not None}
        
    except Exception as e:
        return {"status": "error", "message": f"Invalid filter parameters: {str(e)}"}

    try:
        # Connect to the tasks database
        conn = connect_db(tasks_db_path)
        cursor = conn.cursor()

        # Build the SQL query dynamically based on provided filters
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        for key, value in validated_filters.items():
            if key == 'tags':
                for tag in value:
                    query += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
                continue

            if key in ['working_dt', 'due_dt']:
                try:
                    value = parse_date(value)
                except ValueError:
                    return {"status": "error", "message": f"Invalid date format for {key}: {value}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"}
            query += f" AND {key} = ?"
            params.append(value)
        
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        tasks = []

        for row in rows:
            task = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "due_dt": row[6],
                "working_dt": row[7],
                "duration_mins": row[8],
                "priority": row[9],
                "tags": row[10].split(',') if row[10] else []
            }
            tasks.append(task)

        return {
            "status": "success",
            "tasks": tasks if tasks else [],
            "count": len(tasks)
        }

    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}
    
    except Exception as e:
        return {"status": "error", "message": f"Error retrieving tasks: {str(e)}"}
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    filters = {
        'working_dt': "2025-06-04"
    }
    tasks = get_tasks(filters)
    print(tasks)