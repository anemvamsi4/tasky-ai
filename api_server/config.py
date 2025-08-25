import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # WhatsApp Configuration
    VERIFY_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_APP_SECRET: str
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SESSIONS_DATABASE_URL: str
    
    # Google ADK Configuration
    GOOGLE_PROJECT_ID: str
    GOOGLE_API_KEY: str