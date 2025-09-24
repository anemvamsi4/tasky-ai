import json
import logging

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from config import _settings
from api_server.whatsapp import parse_whatsapp_message, send_whatsapp_message, process_whatsapp_audio_message
from api_server.database import get_user_id_by_phone
from api_server.tasky_ai import call_tasky
from api_server.utils import verify_whatsapp_signature, is_valid_whatsapp_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if not all([hub_mode, hub_verify_token, hub_challenge]):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing query parameters")
    
    if hub_mode == "subscribe" and hub_verify_token == _settings.VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain", status_code=HTTP_200_OK)
    
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Verification failed")

@app.post("/webhook")
async def handle_webhook(request: Request):
    body_bytes = await request.body()

    try:
        new_request = StarletteRequest(scope=request.scope, receive=request._receive)
        setattr(new_request, '_body', body_bytes)

        verified = await verify_whatsapp_signature(new_request, _settings)
        if not verified:
            logger.warning("Invalid WhatsApp signature")
            return JSONResponse(status_code=HTTP_403_FORBIDDEN,
                                content={"status": "error", "detail": "Invalid signature"})
        
    except Exception as e:
        logger.error(f"Error verifying signature: {e}", exc_info=True)
        return JSONResponse(status_code=HTTP_403_FORBIDDEN,
                            content={"status": "error", "detail": "Signature verification error"})
    
    try:
        body = json.loads(body_bytes)
    except ValueError:
        logger.error("Invalid JSON payload")
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={"status": "error", "detail": "Invalid JSON payload"})
    
    if not is_valid_whatsapp_message(body):
        logger.info("Received non-message event, ignoring")
        return JSONResponse(status_code=HTTP_200_OK,
                            content={"status": "ignored", "detail": "Non-message event"})
    
    logger.info(f"Received valid WhatsApp message: {body}")

    try:
        data = parse_whatsapp_message(body)

        contact_name = data.get("username")
        phone_number = data.get("phone_number")
        message_text = data.get("message")
        message_type = data.get("type", "text")
        audio_id = data.get("audio_id")

        user_id = get_user_id_by_phone(
            phone_number, contact_name
        )

        # Process audio messages
        if message_type == "audio" and audio_id:
            logger.info(f"Processing audio message from {contact_name} ({phone_number})")
            
            # Transcribe the audio message
            transcription = await process_whatsapp_audio_message(audio_id, _settings)
            
            if transcription:
                message_text = transcription
                logger.info(f"Audio transcribed successfully: {transcription[:100]}...")

                await send_whatsapp_message(
                    phone_number=phone_number,
                    message=f"You said: \n{transcription}",
                    settings=_settings
                )
            else:
                logger.error("Failed to transcribe audio message")
                await send_whatsapp_message(
                    phone_number=phone_number,
                    message="Sorry, I couldn't process your audio message. Please try sending a text message instead.",
                    settings=_settings
                )
                return JSONResponse(status_code=HTTP_200_OK,
                                    content={"status": "error", "detail": "Audio transcription failed"})

        # Skip processing if no message text (for non-text, non-audio messages)
        if not message_text:
            logger.info(f"No message text found for message type: {message_type}")
            return JSONResponse(status_code=HTTP_200_OK,
                                content={"status": "ignored", "detail": "No processable content"})

        # Call Tasky agent
        agent_response = await call_tasky(
            user_id=user_id,
            message=message_text,
            settings=_settings
        )

        await send_whatsapp_message(
            phone_number=phone_number,
            message=agent_response,
            settings=_settings
        )

        return JSONResponse(status_code=HTTP_200_OK,
                            content={"status": "success", "detail": "Message processed"})
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return JSONResponse(status_code=HTTP_200_OK,
                            content={"status": "error", "detail": "Message processing error"})

if __name__ == "__main__":
    port = _settings.PORT or 8080
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)