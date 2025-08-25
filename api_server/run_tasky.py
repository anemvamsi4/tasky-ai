import logging
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from api_server.config import Settings
from tasky_agent import root_agent

logger = logging.getLogger(__name__)

async def call_tasky(user_id: str, message: str, settings: Settings) -> str:
    """
    Execute Tasky agent with user message and return response.
    
    Args:
        user_id: Unique identifier for the user
        message: User's input message
        settings: Application settings
    
    Returns:
        str: Agent's response message
        
    Raises:
        Exception: If agent fails to generate response
    """
    try:
        runner = _initialize_runner(settings.SESSIONS_DATABASE_URL)
        session_id = get_session_id(user_id, settings.SESSIONS_DATABASE_URL)
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=_create_user_message(message)
        ):
            if event.is_final_response():
                return event.content.parts[0].text
                
        raise Exception("No response generated from agent")
        
    except Exception as e:
        logger.error(f"Error in call_tasky: {str(e)}", exc_info=True)
        raise

def get_session_id(user_id: str, db_url: str) -> str:
    """
    Get or create a session ID for the user.
    
    Args:
        user_id: Unique identifier for the user
        db_url: Database connection URL
        
    Returns:
        str: Session ID
    """
    try:
        session_service = DatabaseSessionService(db_url=db_url)
        session = session_service.get_session(
            app_name='tasky-ai',
            user_id=user_id
        )
        
        if not session:
            session = session_service.create_session(
                app_name='tasky-ai',
                user_id=user_id
            )
            
        return session.session_id
        
    except Exception as e:
        logger.error(f"Error in get_session_id: {str(e)}", exc_info=True)
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