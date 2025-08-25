from typing import Any, Dict
import hmac
import hashlib
import logging
from fastapi import HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN

from config import Settings

logger = logging.getLogger(__name__)

def is_valid_whatsapp_message(body: Dict[str, Any]) -> bool:
    """Validate if the incoming request is a valid WhatsApp message."""
    try:
        return bool(
            body.get("object")
            and body.get("entry")
            and body["entry"][0].get("changes")
            and body["entry"][0]["changes"][0].get("value")
            and body["entry"][0]["changes"][0]["value"].get("messages")
        )
    except (KeyError, IndexError):
        return False

async def verify_whatsapp_signature(request: Request, settings: Settings):
    """Verify WhatsApp signature middleware."""
    signature = request.headers.get("x-hub-signature-256")
    if not signature:
        logger.warning("Missing signature in request")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No signature found"
        )

    try:

        # Get raw body
        body = await request.body()
        
        # Create expected signature
        expected_signature = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        if not hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        ):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )
        
        return True

    except Exception as e:
        logger.error(f"Signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Signature verification failed"
        )