from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class automatically loads configuration from .env files and
    environment variables, with validation to make sure everything
    is set up correctly before the app starts.
    """

    PORT : int = 8080

    # Google Cloud Configuration for Secret Manager
    GOOGLE_CLOUD_PROJECT_ID: Optional[str] = None
    
    # Google ADK Configuration
    GOOGLE_API_KEY: str = Field(..., min_length=1)
    GOOGLE_GENAI_USE_VERTEXAI: bool = False

    # Supabase Configuration
    SUPABASE_URL: str = Field(..., min_length=1)
    SUPABASE_KEY: str = Field(..., min_length=1)
    SESSIONS_DATABASE_URL: str = Field(..., min_length=1)

    # Meta Configuration
    VERIFY_TOKEN: str = Field(..., min_length=1)
    WHATSAPP_PHONE_NUMBER_ID: str = Field(..., min_length=1)
    WHATSAPP_ACCESS_TOKEN: str = Field(..., min_length=1)
    WHATSAPP_APP_SECRET: str = Field(..., min_length=1)

    @validator('SUPABASE_URL')
    def validate_supabase_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('SUPABASE_URL must start with http:// or https://')
        return v

    @validator('SESSIONS_DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('SESSIONS_DATABASE_URL must be a valid PostgreSQL URL')
        return v
    
    def get_dynamic_prompt(self, prompt_type: str) -> str:
        """Get dynamic prompts from Secret Manager or fallback to defaults."""
        if not self.GOOGLE_CLOUD_PROJECT_ID:
            logger.info(f"No Google Cloud Project ID, using default prompt for {prompt_type}")
            return self._get_default_prompt(prompt_type)
        
        try:
            from api_server.secret_manager import get_secret_manager, PromptManager
            
            secret_manager = get_secret_manager(self.GOOGLE_CLOUD_PROJECT_ID)
            if not secret_manager:
                return self._get_default_prompt(prompt_type)
                
            prompt_manager = PromptManager(secret_manager)
            
            if prompt_type == 'tasky_system':
                return prompt_manager.get_tasky_system_prompt()
            elif prompt_type == 'daily_summary':
                return prompt_manager.get_daily_summary_prompt()
            else:
                return self._get_default_prompt(prompt_type)
                
        except Exception as e:
            logger.error(f"Error retrieving prompt from Secret Manager: {e}")
            return self._get_default_prompt(prompt_type)
    
    def _get_default_prompt(self, prompt_type: str) -> str:
        """Get default hardcoded prompts as fallback."""
        if prompt_type == 'tasky_system':
            return """
You are a task manager agent. Your job is to help users manage their tasks effectively.
You can create, retrieve, update, and delete tasks based on user requests.

CURRENT DATETIME: {CURRENT_DATETIME}

USER PREFERENCES:
    - When I provide a datetime, consider it as the working datetime and also due date for the task.
    - Always set deadline datetime and Working datetime for each task.
    - Always set deadline datetime to working datetime, unless specified otherwise.
    - If I don't specify a datetime, use the current date.
    - Prioritize tasks based on due dates and then by priority levels, but dumbly do that and try thinking based on the context of the tasks too.
    - If you're unsure about the priority mention both the due date and priority level in your response and ask me to provide more details.

INSTRUCTIONS:
1. When a user asks to create a task, use the `create_tasks` tool.
2. When a user asks to read/ retrieve tasks, use the `get_tasks` tool.
3. When a user asks to update tasks, use the `update_tasks` tool and to get Task IDs, use the `get_tasks` tool first before updating tasks.
4. When a user asks to delete tasks, use the `delete_tasks` tool and to get Task IDs, use the `get_tasks` tool first before deleting tasks.
5. Never show Task IDs, User IDs, or any other internal identifiers in your responses to the user.
6. If user only provides weekday, calculate the next weekday date based on the current datetime shown above.

- Your responses should be conversational and clear to the user, without specifying unnecessary details about the tools, their parameters or other Intenal details that are not relevant to the user.
- Your responses must use new-lines to separate different parts of the response in a proper format and should be easy to read.
- If you need to ask the user for more information, do so clearly and politely.
"""
        elif prompt_type == 'daily_summary':
            return """
You are an AI assistant that generates a clear and concise daily summary for a user named {user_name}.
Today's date is {date}.
Here are the tasks for today:
{tasks}

INSTRUCTIONS:
- If user name is not provided accurately, use a generic greeting.
- Summarize the tasks in a short and concise manner.
- Highlight any important or urgent tasks.
- Generate in Plain Text only, no markdown and seperate sections with new lines.
- Keep it Short and clear with simple language.
- Conclude with a motivational statement encouraging the user to complete their tasks in a creative way.
- Avoid using bullet points or numbered lists.
"""
        return ""

_settings = Settings()