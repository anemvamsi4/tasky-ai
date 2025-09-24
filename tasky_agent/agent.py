from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from datetime import datetime

from tasky_agent.tools.create_tasks import create_tasks
from tasky_agent.tools.get_tasks import get_tasks
from tasky_agent.tools.update_tasks import update_tasks
from tasky_agent.tools.delete_tasks import delete_tasks

from config import Settings, _settings

def update_current_datetime(callback_context: CallbackContext):
    """
    Keep the AI updated with the current time and date.
    
    This runs before every conversation so the AI always knows what day it is.
    Pretty important for a task manager that needs to understand "tomorrow" and "next week"!
    """
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    weekday = now.strftime("%A")
    callback_context.state["CURRENT_DATETIME"] = f"{formatted_time} ({weekday})"

def get_dynamic_system_prompt() -> str:
    """
    Get the instructions that tell our AI how to behave.
    
    These can be updated dynamically through Google Cloud Secret Manager,
    which means we can improve the AI's personality without redeploying code.
    """
    prompt = _settings.get_dynamic_prompt('tasky_system')
    return prompt.format(CURRENT_DATETIME="{CURRENT_DATETIME}")

# This is our main AI agent - think of it as the brain of the whole system
task_manager_agent = Agent(
    name="task_manager_agent",
    model="gemini-2.0-flash",  # Using Google's latest and greatest AI model
    description="A task manager agent that helps users create and manage tasks.",
    instruction=get_dynamic_system_prompt(),
    tools=[
        create_tasks,    # Let the AI create new tasks
        get_tasks,       # Let the AI retrieve and show tasks  
        update_tasks,    # Let the AI modify existing tasks
        delete_tasks     # Let the AI remove completed tasks
    ],
    before_agent_callback=update_current_datetime,  # Always know what time it is
)

# Make it easy to import this agent from other files
root_agent = task_manager_agent