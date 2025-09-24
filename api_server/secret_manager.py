import logging
from typing import Optional
from google.cloud import secretmanager
from google.api_core import exceptions

logger = logging.getLogger(__name__)

class SecretManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except exceptions.NotFound:
            logger.warning(f"Secret not found: {secret_name}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
            return None

_secret_manager = None

def get_secret_manager(project_id: str, **kwargs) -> SecretManager:
    global _secret_manager
    if _secret_manager is None and project_id:
        _secret_manager = SecretManager(project_id)
    return _secret_manager

class PromptManager:
    def __init__(self, secret_manager: SecretManager):
        self.secret_manager = secret_manager
    
    def get_tasky_system_prompt(self) -> str:
        if self.secret_manager:
            prompt = self.secret_manager.get_secret("tasky-system-prompt")
            if prompt:
                return prompt
        return self._get_default_tasky_prompt()
    
    def get_daily_summary_prompt(self) -> str:
        if self.secret_manager:
            prompt = self.secret_manager.get_secret("daily-summary-prompt")
            if prompt:
                return prompt
        return self._get_default_daily_summary_prompt()
    
    def _get_default_tasky_prompt(self) -> str:
        return """
You are a task manager agent. Your job is to help users manage their tasks effectively.
You can create, retrieve, update, and delete tasks based on user requests.

CURRENT DATETIME: {CURRENT_DATETIME}

USER PREFERENCES:
    - When I provide a datetime, consider it as the working datetime and also due date for the task.
    - Always set deadline datetime and Working datetime for each task.
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
    
    def _get_default_daily_summary_prompt(self) -> str:
        """Default daily summary prompt."""
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