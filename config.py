from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import Optional

load_dotenv()

class Settings(BaseSettings):

    PORT : int = 8080
    
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

_settings = Settings()