from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from datetime import datetime

from tasky_agent.tools.create_tasks import create_tasks
from tasky_agent.tools.get_tasks import get_tasks
from tasky_agent.tools.update_tasks import update_tasks
from tasky_agent.tools.delete_tasks import delete_tasks

from config import Settings, _settings

def update_current_datetime(callback_context: CallbackContext):
    """Update the current datetime in the agent's state before each execution."""
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    weekday = now.strftime("%A")
    callback_context.state["CURRENT_DATETIME"] = f"{formatted_time} ({weekday})"

def get_dynamic_system_prompt() -> str:
    """Get the dynamic system prompt from Secret Manager or fallback."""
    prompt = _settings.get_dynamic_prompt('tasky_system')
    return prompt.format(CURRENT_DATETIME="{CURRENT_DATETIME}")

task_manager_agent = Agent(
    name="task_manager_agent",
    model="gemini-2.0-flash",
    description="A task manager agent that helps users create and manage tasks.",
    instruction=get_dynamic_system_prompt(),
    tools=[
        create_tasks,
        get_tasks,
        update_tasks,
        delete_tasks
    ],
    before_agent_callback=update_current_datetime,
)

root_agent = task_manager_agent