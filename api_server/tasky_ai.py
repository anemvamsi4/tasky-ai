import logging
from uuid import UUID
from google.genai import Client
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from config import Settings, _settings
from tasky_agent import root_agent

logger = logging.getLogger(__name__)

async def call_tasky(user_id: UUID, message: str, settings: Settings) -> str:
    """
    Execute Tasky agent with user message and return response.
    
    Args:
        user_id: Unique identifier for the user as UUID
        message: User's input message
        settings: Application settings
    
    Returns:
        str: Agent's response message
        
    Raises:
        Exception: If agent fails to generate response
    """
    try:
        # Convert UUID to string to avoid type conflicts
        user_id_str = str(user_id)
        
        runner = _initialize_runner(settings.SESSIONS_DATABASE_URL)
        session_id = await get_session_id(user_id, settings.SESSIONS_DATABASE_URL)
        
        async for event in runner.run_async(
            user_id=user_id_str,
            session_id=session_id,
            new_message=_create_user_message(message)
        ):
            if event.is_final_response():
                if event.content and event.content.parts and event.content.parts[0].text:
                    return event.content.parts[0].text
                else:
                    logger.warning("Final response received but no text content available")
                
        raise Exception("No valid response generated from agent")
        
    except Exception as e:
        logger.error(f"Error in call_tasky: {str(e)}")
        raise

async def get_session_id(user_id: UUID, db_url: str) -> str:
    """
    Get or create a session ID for the user.
    
    Args:
        user_id: Unique identifier for the user
        db_url: Database connection URL
        
    Returns:
        str: Session ID
    """
    try:
        # Convert UUID to string
        user_id_str = str(user_id)
        
        session_service = DatabaseSessionService(db_url=db_url)
        session = await session_service.get_session(
            app_name='tasky-ai',
            user_id=user_id_str,
            session_id=user_id_str
        )
        
        if not session:
            session = await session_service.create_session(
                app_name='tasky-ai',
                user_id=user_id_str,
                session_id=user_id_str
            )
            
        return session.id
        
    except Exception as e:
        logger.error(f"Error in get_session_id: {str(e)}")
        raise

def _initialize_runner(db_url: str) -> Runner:
    """Initialize the Runner with required configurations."""
    return Runner(
        app_name='tasky-ai',
        agent=root_agent,
        session_service=DatabaseSessionService(db_url=db_url)
    )

def _create_user_message(message: str) -> types.Content:
    """Create a formatted user message."""
    return types.Content(
        role='user',
        parts=[types.Part(text=message)]
    )

def generate_daily_summary(date: str, user_name: str, tasks: list) -> str:
    """Generate a daily summary using Google Generative AI."""
    
    # Get dynamic prompt from Secret Manager
    prompt_template = _settings.get_dynamic_prompt('daily_summary')
    
    prompt = prompt_template.format(
        date=date,
        user_name=user_name,
        tasks=tasks
    )

    try:
        genai_client = Client(api_key=_settings.GOOGLE_API_KEY)
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text
    except Exception as e:
        raise RuntimeError(f"Failed to generate summary: {str(e)}")