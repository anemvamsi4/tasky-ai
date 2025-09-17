from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Google ADK Configuration
    GOOGLE_API_KEY: str
    GOOGLE_GENAI_USE_VERTEXAI: bool

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SESSIONS_DATABASE_URL: str