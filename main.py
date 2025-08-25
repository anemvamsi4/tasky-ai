import json
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Depends
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
settings = Settings()  # Load settings from config

@app.get("/webhook")
async def verify_webhook(
    mode: Optional[str] = None,
    token: Optional[str] = None,
    challenge: Optional[str] = None
):
    """Handle webhook verification from WhatsApp."""
    if not all([mode, token]):
        logger.info("Missing parameters in verification request")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Missing parameters"
        )

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    
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
    except json.JSONDecodeError:
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

        # Parse recieved message from user 
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
            message=message_text
        )

        # Send response back to WhatsApp
        await send_whatsapp_message(phone_number, agent_response)
        return JSONResponse(content={"status": "ok"}, status_code=HTTP_200_OK)
    
    logger.warning("Invalid WhatsApp API event")
    raise HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail="Not a WhatsApp API event"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)