import logging
import tempfile
import os
from typing import Dict, Any, Optional, Tuple

import aiohttp
from groq import AsyncGroq
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from config import Settings, _settings

logger = logging.getLogger(__name__)

def parse_whatsapp_message(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse username, phone number and message from WhatsApp webhook payload.
    
    Args:
        body: The webhook request body from WhatsApp
        
    Returns:
        Dictionary containing username, phone number, message text, message type, and audio_id if applicable
    """
    try:
        # Extract entry
        entry = body.get("entry", [])
        if not entry or len(entry) == 0:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        # Extract changes
        changes = entry[0].get("changes", [])
        if not changes or len(changes) == 0:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        # Extract value
        value = changes[0].get("value", {})
        if not value:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        # Extract messages
        messages = value.get("messages", [])
        if not messages or len(messages) == 0:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        # Extract the first message
        message_data = messages[0]
        
        # Get the sender's phone number
        phone_number = message_data.get("from", "")
        
        # Get message type and content
        message_type = message_data.get("type", "text")
        message_text = ""
        audio_id = None
        
        if message_type == "text":
            message_text = message_data.get("text", {}).get("body", "")
        elif message_type == "audio":
            audio_id = message_data.get("audio", {}).get("id", "")
            message_text = ""  # Will be filled after speech-to-text conversion
            
        # Get contact name if available
        contact_name = "Unknown User"
        contacts = value.get("contacts", [])
        if contacts and len(contacts) > 0:
            contact_name = contacts[0].get("profile", {}).get("name", "Unknown User")
        
        return {
            "username": contact_name,
            "phone_number": phone_number,
            "message": message_text,
            "type": message_type,
            "audio_id": audio_id
        }
    except (KeyError, IndexError, TypeError) as e:
        # Return default values on error
        return {
            "username": "Unknown User",
            "phone_number": "",
            "message": "",
            "type": "text",
            "audio_id": None
        }

async def download_audio_from_whatsapp(audio_id: str, settings: Settings) -> Optional[bytes]:
    """
    Download audio file from WhatsApp using media ID.
    
    Args:
        audio_id: The WhatsApp media ID for the audio file
        settings: Application settings containing WhatsApp API credentials
        
    Returns:
        bytes: Audio file content, or None if download failed
    """
    try:
        # First, get the media URL
        url = f"https://graph.facebook.com/v17.0/{audio_id}"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"
        }
        
        async with aiohttp.ClientSession() as session:
            # Get media info
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get media info (status {response.status})")
                    return None
                    
                media_info = await response.json()
                media_url = media_info.get("url")
                
                if not media_url:
                    logger.error("No media URL found in response")
                    return None
            
            # Download the actual audio file
            async with session.get(media_url, headers=headers) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Failed to download audio file (status {response.status})")
                    return None
                    
    except Exception as e:
        logger.error(f"Error downloading audio from WhatsApp: {e}")
        return None

async def transcribe_audio_with_groq(audio_data: bytes, settings: Settings) -> Optional[str]:
    """
    Transcribe audio using Groq's speech-to-text service.
    
    Args:
        audio_data: The audio file content as bytes
        settings: Application settings containing Groq API key
        
    Returns:
        str: Transcribed text, or None if transcription failed
    """
    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the audio
            with open(temp_file_path, "rb") as audio_file:
                transcription = await client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    response_format="text"
                )
                
                # The response should be a string with the transcribed text
                return transcription.strip() if transcription else None
                
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error transcribing audio with Groq: {e}")
        return None

async def process_whatsapp_audio_message(audio_id: str, settings: Settings) -> Optional[str]:
    """
    Download and transcribe a WhatsApp audio message.
    
    Args:
        audio_id: The WhatsApp media ID for the audio file
        settings: Application settings
        
    Returns:
        str: Transcribed text, or None if processing failed
    """
    logger.info(f"Processing audio message with ID: {audio_id}")
    
    # Download the audio file
    audio_data = await download_audio_from_whatsapp(audio_id, settings)
    if not audio_data:
        logger.error("Failed to download audio file")
        return None
    
    logger.info(f"Downloaded audio file ({len(audio_data)} bytes)")

    if len(audio_data) > 25 * 1024 * 1024:
        logger.warning(f"Audio file too large: {len(audio_data)} bytes")
    
    # Transcribe the audio
    transcription = await transcribe_audio_with_groq(audio_data, settings)
    if not transcription:
        logger.error("Failed to transcribe audio")
        return None
    
    await send_whatsapp_message(
        phone_number="",
        message=f"You said: \n{transcription}",
        settings=settings
    )
    
    logger.info(f"Transcribed audio: {transcription[:100]}...")
    return transcription

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