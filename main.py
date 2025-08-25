import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from api_server.whatsapp import parse_whatsapp_message, send_whatsapp_message
from api_server.run_tasky import call_tasky
from api_server.utils import is_valid_whatsapp_message, verify_whatsapp_signature
from api_server.database import get_user_id_by_phone

from api_server.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
settings = Settings()

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Handle webhook verification from WhatsApp."""
    # Log the received parameters
    logger.info(f"Received verification request - Mode: {hub_mode}, Token: {hub_verify_token}, Challenge: {hub_challenge}")
    
    if not all([hub_mode, hub_verify_token, hub_challenge]):
        logger.info("Missing parameters in verification request")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Missing parameters"
        )

    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.warning("Webhook verification failed")
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Verification failed"
    )

@app.post("/webhook")
async def handle_webhook(
    request: Request,
    verified: bool = Depends(verify_whatsapp_signature)
):
    """Handle incoming webhook events from WhatsApp."""
    if not verified:
        logger.warning("Failed WhatsApp signature verification")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, 
            detail="Invalid signature"
        )

    try:
        body = await request.json()
    except ValueError:
        logger.error("Failed to decode JSON")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    # Handle WhatsApp status updates
    if (body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")):
        logger.info("Received WhatsApp status update")
        return JSONResponse(content={"status": "ok"}, status_code=HTTP_200_OK)

    # Process WhatsApp messages
    if is_valid_whatsapp_message(body):

        # Parse received message from user 
        data = await parse_whatsapp_message(body)

        contact_name = data.get("username")
        phone_number = data.get("phone_number")
        message_text = data.get("message")

        user_id = get_user_id_by_phone(
            phone_number=phone_number,
            username=contact_name
        )

        # Call Tasky Agent and get response
        agent_response = await call_tasky(
            user_id=user_id,
            message=message_text,
            settings=settings
        )

        # Send response back to WhatsApp
        await send_whatsapp_message(phone_number, agent_response, settings)
        return JSONResponse(content={"status": "ok"}, status_code=HTTP_200_OK)
    
    logger.warning("Invalid WhatsApp API event")
    raise HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail="Not a WhatsApp API event"
    )

if __name__ == "__main__":
    # Use PORT environment variable with default of 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)