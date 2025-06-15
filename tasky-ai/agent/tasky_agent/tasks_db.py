import sqlite3
from pathlib import Path

def create_tasks_db(db_path):
    """Create the tasks database if it doesn't exist."""
    db_path = Path(db_path)
    
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending' NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed')),
            created_at DATETIME DEFAULT (datetime('now')),
            updated_at DATETIME DEFAULT (datetime('now')),
            due_dt DATETIME,
            working_dt DATETIME,
            duration_mins INTEGER DEFAULT 0,
            priority INTEGER CHECK(priority BETWEEN 1 AND 3),
            tags TEXT
        )
    """)
    
    conn.commit()
    conn.close()