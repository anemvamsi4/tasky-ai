import sqlite3
from datetime import datetime
import os
from supabase import create_client, Client

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
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
    supabase: Client = create_client(url, key)
    return supabase