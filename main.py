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
    if not all([hub_mode, hub_verify_token, hub_challenge]):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Missing parameters"
        )

    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Verification failed"
    )

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook events from WhatsApp."""
    # Store the original request body for signature verification
    body_bytes = await request.body()
    
    # Verify signature
    try:
        from starlette.requests import Request as StarletteRequest
        new_request = StarletteRequest(
            scope=request.scope,
            receive=request._receive
        )
        setattr(new_request, "_body", body_bytes)
        
        verified = await verify_whatsapp_signature(new_request, settings)
        if not verified and not settings.DEBUG_MODE:
            return JSONResponse(
                content={"status": "error", "detail": "Invalid signature"}, 
                status_code=HTTP_403_FORBIDDEN
            )
    except Exception as e:
        if not settings.DEBUG_MODE:
            return JSONResponse(
                content={"status": "error", "detail": "Signature verification failed"}, 
                status_code=HTTP_403_FORBIDDEN
            )
    
    try:
        # Parse the body as JSON
        body = json.loads(body_bytes)
    except ValueError:
        return JSONResponse(
            content={"status": "error", "detail": "Invalid JSON"}, 
            status_code=HTTP_400_BAD_REQUEST
        )

    # Handle WhatsApp status updates
    if (body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")):
        return JSONResponse(content={"status": "ok"}, status_code=HTTP_200_OK)

    # Process WhatsApp messages
    if is_valid_whatsapp_message(body):
        try:
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
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return JSONResponse(
                content={"status": "ok"}, 
                status_code=HTTP_200_OK
            )
    
    # Return 200 even for invalid events to prevent WhatsApp from deactivating the webhook
    return JSONResponse(
        content={"status": "ok"}, 
        status_code=HTTP_200_OK
    )

if __name__ == "__main__":
    # Use PORT environment variable with default of 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)