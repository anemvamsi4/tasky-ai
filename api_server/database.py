import logging
from uuid import UUID

from fastapi import HTTPException
from postgrest import APIError
from tasky_agent.utils import connect_db

logger = logging.getLogger(__name__)

def get_user_id_by_phone(phone_number: str, username: str) -> UUID:
    """
    Retrieve or create user ID from Supabase users table based on phone number.
    
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
        
        # Query the users table for the phone number
        response = supabase.table('users').select('id').eq('phone_number', phone_number).execute()
        
        if response.data:
            return UUID(response.data[0]['id'])
        
        # If user doesn't exist, create new user
        new_user = {
            'phone_number': phone_number,
            'username': username
        }
        
        try:
            response = supabase.table('users').insert(new_user).execute()
            return UUID(response.data[0]['id'])
        except APIError as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create user record"
            )
        
    except Exception as e:
        logger.error(f"Error in get_user_id_by_phone: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )