from google.adk.agents import Agent

from .prompt import TASK_MANAGER_PROMPT, DEFAULT_USER_PREFERENCES
from .tools.get_datetime_now import get_datetime_now
from .tools.create_tasks import create_tasks
from .tools.get_tasks import get_tasks
from .tools.update_tasks import update_tasks
from .tools.delete_tasks import delete_tasks

task_manager_agent = Agent(
    name="task_manager_agent",
    model="gemini-2.0-flash",
    description="A task manager agent that helps users create and manage tasks.",
    instruction = TASK_MANAGER_PROMPT.format(
        USER_PREFERENCES = DEFAULT_USER_PREFERENCES
    ),
    
    tools=[
        get_datetime_now,
        create_tasks,
        get_tasks,
        update_tasks,
        delete_tasks
    ],
)

root_agent = task_manager_agent