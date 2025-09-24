import logging
import tempfile
import os
from typing import Dict, Any, Optional, Tuple

import aiohttp
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from config import Settings, _settings

from google.cloud import speech
import asyncio
import concurrent.futures
import io

logger = logging.getLogger(__name__)

def parse_whatsapp_message(body: Dict[str, Any]) -> Dict[str, Any]:
    """Extract useful data from WhatsApp's complex webhook payload."""
    try:
        entry = body.get("entry", [])
        if not entry:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        changes = entry[0].get("changes", [])
        if not changes:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        value = changes[0].get("value", {})
        if not value:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        messages = value.get("messages", [])
        if not messages:
            return {"username": "Unknown User", "phone_number": "", "message": "", "type": "text", "audio_id": None}
            
        message_data = messages[0]
        phone_number = message_data.get("from", "")
        message_type = message_data.get("type", "text")
        message_text = ""
        audio_id = None
        
        if message_type == "text":
            message_text = message_data.get("text", {}).get("body", "")
        elif message_type == "audio":
            audio_id = message_data.get("audio", {}).get("id", "")
            
        contact_name = "Unknown User"
        contacts = value.get("contacts", [])
        if contacts:
            contact_name = contacts[0].get("profile", {}).get("name", "Unknown User")
        
        return {
            "username": contact_name,
            "phone_number": phone_number,
            "message": message_text,
            "type": message_type,
            "audio_id": audio_id
        }
    except (KeyError, IndexError, TypeError):
        return {
            "username": "Unknown User",
            "phone_number": "",
            "message": "",
            "type": "text",
            "audio_id": None
        }

async def download_audio_from_whatsapp(audio_id: str, settings: Settings) -> Optional[bytes]:
    """Download audio file from WhatsApp using the media ID."""
    try:
        url = f"https://graph.facebook.com/v17.0/{audio_id}"
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get media info (status {response.status})")
                    return None
                    
                media_info = await response.json()
                media_url = media_info.get("url")
                
                if not media_url:
                    logger.error("No media URL found in response")
                    return None
            
            async with session.get(media_url, headers=headers) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Failed to download audio file (status {response.status})")
                    return None
                    
    except Exception as e:
        logger.error(f"Error downloading audio from WhatsApp: {e}")
        return None

async def transcribe_audio_with_google(audio_data: bytes, settings: Settings) -> Optional[str]:
    """Convert audio to text using Google Speech-to-Text API."""
    def _transcribe_sync(audio_data: bytes) -> Optional[str]:
        try:
            client = speech.SpeechClient()
            audio = speech.RecognitionAudio(content=audio_data)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,
                language_code="en-US",
                alternative_language_codes=["en-IN", "hi-IN", "te-IN"],
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False,
                use_enhanced=True,
                model="latest_long",
            )
            
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                transcription = response.results[0].alternatives[0].transcript
                confidence = response.results[0].alternatives[0].confidence
                
                logger.info(f"Transcription confidence: {confidence:.2f}")
                
                if confidence < 0.3:
                    logger.warning(f"Low confidence transcription: {confidence:.2f}")
                
                return transcription.strip() if transcription else None
            else:
                logger.warning("No transcription results from Google Speech-to-Text")
                return None
                
        except Exception as e:
            logger.error(f"Error in sync transcription: {type(e).__name__}: {e}")
            return None
    
    try:
        logger.info("Sending audio to Google Speech-to-Text API...")
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, _transcribe_sync, audio_data)
            return result
            
    except Exception as e:
        logger.error(f"Error transcribing audio: {type(e).__name__}: {e}")
        return None

async def process_whatsapp_audio_message(audio_id: str, settings: Settings) -> Optional[str]:
    """Process WhatsApp audio message and return transcription."""
    logger.info(f"Processing audio message with ID: {audio_id}")
    
    audio_data = await download_audio_from_whatsapp(audio_id, settings)
    if not audio_data:
        logger.error("Failed to download audio file")
        return None
    
    logger.info(f"Downloaded audio file ({len(audio_data)} bytes)")
    
    transcription = await transcribe_audio_with_google(audio_data, settings)
    
    if transcription and len(transcription.strip()) > 0:
        logger.info(f"Transcription success: '{transcription[:100]}{'...' if len(transcription) > 100 else ''}'")
        return transcription.strip()
    
    logger.error("Failed to transcribe audio")
    return None

async def send_whatsapp_message(phone_number: str, message: str, settings: Settings) -> bool:
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