import logging
from typing import Dict, Any

import aiohttp
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from config import Settings, _settings

logger = logging.getLogger(__name__)

def parse_whatsapp_message(body: Dict[str, Any]) -> Dict[str, str]:
    """
    Parse username, phone number and message from WhatsApp webhook payload.
    
    Args:
        body: The webhook request body from WhatsApp
        
    Returns:
        Dictionary containing username, phone number and message text
    """
    try:
        # Extract entry
        entry = body.get("entry", [])
        if not entry or len(entry) == 0:
            return {"username": "Unknown User", "phone_number": "", "message": ""}
            
        # Extract changes
        changes = entry[0].get("changes", [])
        if not changes or len(changes) == 0:
            return {"username": "Unknown User", "phone_number": "", "message": ""}
            
        # Extract value
        value = changes[0].get("value", {})
        if not value:
            return {"username": "Unknown User", "phone_number": "", "message": ""}
            
        # Extract messages
        messages = value.get("messages", [])
        if not messages or len(messages) == 0:
            return {"username": "Unknown User", "phone_number": "", "message": ""}
            
        # Extract the first message
        message_data = messages[0]
        
        # Get the sender's phone number
        phone_number = message_data.get("from", "")
        
        # Get the message text
        message_text = ""
        if message_data.get("type") == "text":
            message_text = message_data.get("text", {}).get("body", "")
            
        # Get contact name if available
        contact_name = "Unknown User"
        contacts = value.get("contacts", [])
        if contacts and len(contacts) > 0:
            contact_name = contacts[0].get("profile", {}).get("name", "Unknown User")
        
        return {
            "username": contact_name,
            "phone_number": phone_number,
            "message": message_text
        }
    except (KeyError, IndexError, TypeError) as e:
        # Return default values on error
        return {
            "username": "Unknown User",
            "phone_number": "",
            "message": ""
        }

async def send_whatsapp_message(phone_number: str, message: str, settings: Settings) -> bool:
    """
    Send a WhatsApp message to a specified phone number.
    
    Args:
        phone_number: The recipient's phone number
        message: The message text to send
        settings: Application settings containing WhatsApp API credentials and configuration
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return True
                error_text = await response.text()
                truncated_error = error_text[:200] + ("..." if len(error_text) > 200 else "")
                logger.error(f"Failed to send WhatsApp message (status {response.status}): {truncated_error}")
                return False
    except aiohttp.ClientError as e:
        logger.error(f"ClientError while sending WhatsApp message: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error ({type(e).__name__}) while sending WhatsApp message: {e}")
        return False