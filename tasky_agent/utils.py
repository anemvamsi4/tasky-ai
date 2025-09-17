from datetime import datetime
from supabase import create_client, Client
from config import Settings

def parse_date(date_str):
    """Parse a date string into a datetime object."""
    try:
        if ' ' in date_str:  # Format with time
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:  # Format with just date
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")

def connect_db():
    """Connect to the Supabase database."""
    settings = Settings()
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return supabase