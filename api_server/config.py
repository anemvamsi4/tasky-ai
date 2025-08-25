import os
from typing import Optional

class Settings:
    # WhatsApp Configuration
    VERIFY_TOKEN: str = os.environ.get("VERIFY_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN: str = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_APP_SECRET: str = os.environ.get("WHATSAPP_APP_SECRET", "")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
    SESSIONS_DATABASE_URL: str = os.environ.get("SESSIONS_DATABASE_URL", "")
    
    # Google ADK Configuration
    GOOGLE_PROJECT_ID: str = os.environ.get("GOOGLE_PROJECT_ID", "")
    GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
    
    def __init__(self):
        required_vars = [
            "VERIFY_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_APP_SECRET",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "GOOGLE_PROJECT_ID",
            "GOOGLE_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(self, var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")