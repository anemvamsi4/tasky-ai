from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from datetime import datetime

from tasky_agent.prompt import TASK_MANAGER_PROMPT, DEFAULT_USER_PREFERENCES
from tasky_agent.tools.create_tasks import create_tasks
from tasky_agent.tools.get_tasks import get_tasks
from tasky_agent.tools.update_tasks import update_tasks
from tasky_agent.tools.delete_tasks import delete_tasks

def update_current_datetime(callback_context: CallbackContext):
    """Update the current datetime in the agent's state before each execution."""
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    weekday = now.strftime("%A")
    callback_context.state["CURRENT_DATETIME"] = f"{formatted_time} ({weekday})"

task_manager_agent = Agent(
    name="task_manager_agent",
    model="gemini-2.0-flash",
    description="A task manager agent that helps users create and manage tasks.",
    instruction=TASK_MANAGER_PROMPT.format(
        USER_PREFERENCES=DEFAULT_USER_PREFERENCES,
        CURRENT_DATETIME="{CURRENT_DATETIME}"
    ),
    tools=[
        create_tasks,
        get_tasks,
        update_tasks,
        delete_tasks
    ],
    before_agent_callback=update_current_datetime,
)

root_agent = task_manager_agent