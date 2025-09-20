from datetime import datetime
from supabase import create_client, Client
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import _settings

def parse_date(date_str):
    """Parse a date string into a datetime object."""
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string cannot be empty or None")
    
    try:
        if ' ' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")

def validate_uuid(uuid_str):
    """Validate if a string is a valid UUID."""
    if not uuid_str or not isinstance(uuid_str, str):
        return False
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, TypeError):
        return False

def connect_db():
    """Connect to the Supabase database."""
    try:
        if not _settings.SUPABASE_URL or not _settings.SUPABASE_KEY:
            raise ValueError("Missing Supabase configuration")
        supabase: Client = create_client(_settings.SUPABASE_URL, _settings.SUPABASE_KEY)
        return supabase
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {str(e)}")