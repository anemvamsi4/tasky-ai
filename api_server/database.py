import logging
from uuid import UUID

from fastapi import HTTPException
from postgrest import APIError
from tasky_agent.utils import connect_db

logger = logging.getLogger(__name__)

def get_user_id_by_phone(phone_number: str, username: str) -> UUID:
    """
    Retrieve user ID from Supabase users table based on phone number.
    If the user does not exist, create a new user and return the new user ID.
    
    Args:
        phone_number (str): Phone number of the user
        username (str): Username of the user
        
    Returns:
        UUID: User ID if found or created
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        # Connect to Supabase
        supabase = connect_db()
        
        response = supabase.table('users').select('id, username, phone_number').eq('phone_number', phone_number).execute()
        response = supabase.table('users').select('id').eq('phone_number', phone_number).execute()
        
        if response.data:
            user_id_str = response.data[0]['id']
            try:
                return UUID(user_id_str)
            except ValueError:
                logger.error(f"Invalid UUID format for user id: {user_id_str}")
                raise HTTPException(
                    status_code=500,
                    detail="Invalid user ID format in database"
                )
        try:
            new_user = {"phone_number": phone_number, "username": username}
            response = supabase.table('users').insert(new_user).execute()
            return UUID(response.data[0]['id'])
        except APIError as e:
            # Check if error is due to unique constraint violation
            if "duplicate key value violates unique constraint" in str(e).lower():
                logger.warning(f"User with phone number {phone_number} already exists. Fetching existing user ID.")
                # Re-query for the user ID
                response = supabase.table('users').select('id').eq('phone_number', phone_number).execute()
                if response.data:
                    user_id_str = response.data[0]['id']
                    try:
                        return UUID(user_id_str)
                    except ValueError:
                        logger.error(f"Invalid UUID format for user id: {user_id_str}")
                        raise HTTPException(
                            status_code=500,
                            detail="Invalid user ID format in database"
                        )
                else:
                    logger.error("User exists but could not retrieve user ID.")
                    raise HTTPException(
                        status_code=500,
                        detail="User exists but could not retrieve user ID."
                    )
            else:
                logger.exception("Failed to create user: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create user record"
                )
        
    except Exception as e:
        logger.exception("Error in get_user_id_by_phone")
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )
def get_users_tasks_by_date(date: str) -> list:
    """
    Get a list of users with their phone numbers and tasks for a specific date.
    
    Args:
        date (str): Date in YYYY-MM-DD format
        
    Returns:
        list: List of dictionaries containing user and task information
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        supabase = connect_db()
        
        logger.info(f"Fetching users and tasks for date: {date}")
        
        # Fetch all users
        users_query = supabase.table("users").select("id, username, phone_number").execute()
        users = users_query.data
        logger.info(f"Found {len(users)} users")
        
        # Fetch all tasks for the date (using date range to handle timezone issues)
        start_of_day = f"{date}T00:00:00"
        end_of_day = f"{date}T23:59:59"
        tasks_query = supabase.table("tasks").select("id, title, description, status, duration_mins, user_id, working_dt, due_dt")\
            .gte("working_dt", start_of_day)\
            .lte("working_dt", end_of_day).execute()
        tasks = tasks_query.data
        logger.info(f"Found {len(tasks)} tasks for date {date}")
        
        # Map tasks to users
        user_map = {user["id"]: user for user in users}
        for user in user_map.values():
            user["tasks"] = []
        
        for task in tasks:
            # Only add task if user exists in user_map
            if task["user_id"] in user_map:
                user_map[task["user_id"]]["tasks"].append(task)
            else:
                logger.warning(f"Task {task['id']} references non-existent user {task['user_id']}")
        
        result = list(user_map.values())
        logger.info(f"Returning {len(result)} users with tasks")
        return result
    
    except APIError as api_error:
        logger.exception(f"Supabase API error in get_users_tasks_by_date: {api_error}")
        raise HTTPException(
            status_code=500,
            detail=f"Database API error: {str(api_error)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error in get_users_tasks_by_date: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user tasks"
        )