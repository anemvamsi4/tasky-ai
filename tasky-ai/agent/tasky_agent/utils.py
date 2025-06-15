import sqlite3
from datetime import datetime

def parse_date(date_str):
    """Parse a date string into a datetime object."""
    try:
        if ' ' in date_str:  # Format with time
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:  # Format with just date
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")

def connect_db(db_path):
    """Connect to the SQLite database."""
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
    sqlite3.register_converter("timestamp", lambda s: datetime.fromisoformat(s.decode('utf-8')))
    
    return conn