DEFAULT_TASKS_DB_PATH = ".tasky/dbs/tasks.db"

class Config:
    def __init__(self):
        self.config = {
            "tasks_db_path": DEFAULT_TASKS_DB_PATH
        }
    
    def get_config(self):
        """
        Returns the current configuration settings.
        """
        return self.config