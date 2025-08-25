import logging
from typing import Dict, Any

import aiohttp
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from api_server.config import Settings

logger = logging.getLogger(__name__)

async def parse_whatsapp_message(body: Dict[str, Any]) -> Dict[str, str]:
    """
    Parse username, phone number and message from WhatsApp webhook payload.
    
    Args:
        body: The webhook request body from WhatsApp
        
    Returns:
        Dictionary containing username, phone number and message text
    """
    try:
        message_data = (body.get("entry", [{}])[0]
                       .get("changes", [{}])[0]
                       .get("value", {})
                       .get("messages", [{}])[0])
        
        # Get the sender's phone number
        phone_number = message_data.get("from", "")
        
        # Get the message text
        message_text = message_data.get("text", {}).get("body", "")
        
        # Get contact name if available
        contact_name = (body.get("entry", [{}])[0]
                       .get("changes", [{}])[0]
                       .get("value", {})
                       .get("contacts", [{}])[0]
                       .get("profile", {})
                       .get("name", "Unknown User"))
        
        return {
            "username": contact_name,
            "phone_number": phone_number,
            "message": message_text
        }
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing WhatsApp message: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, 
                          detail="Invalid message format")

async def send_whatsapp_message(phone_number: str, message: str, settings: Settings) -> bool:
    """
    Send a WhatsApp message to a specified phone number.
    
    Args:
        phone_number: The recipient's phone number
        message: The message text to send
        
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
                logger.error(f"Failed to send WhatsApp message: {await response.text()}")
                return False
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False