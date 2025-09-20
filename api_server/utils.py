from typing import Any, Dict
import hmac
import hashlib
import logging
from fastapi import Request
from starlette.status import HTTP_403_FORBIDDEN

from config import _settings, Settings

logger = logging.getLogger(__name__)

def is_valid_whatsapp_message(body: Dict[str, Any]) -> bool:
    """Validate if the incoming request is a valid WhatsApp message."""
    try:
        # First check the basic structure we expect from WhatsApp
        if not (body.get("entry") and isinstance(body["entry"], list) and len(body["entry"]) > 0):
            return False
            
        entry = body["entry"][0]
        
        # Check for changes field
        if not (entry.get("changes") and isinstance(entry["changes"], list) and len(entry["changes"]) > 0):
            return False
            
        changes = entry["changes"][0]
        
        # Check for value field
        if not changes.get("value"):
            return False
            
        value = changes["value"]
        
        # Check for messages field
        if not (value.get("messages") and isinstance(value["messages"], list) and len(value["messages"]) > 0):
            return False
            
        # Message looks valid
        return True
    except (KeyError, IndexError, TypeError):
        return False

async def verify_whatsapp_signature(request: Request, settings: Settings) -> bool:
    """Verify WhatsApp signature middleware."""
    signature_header = request.headers.get("x-hub-signature-256")
    
    if not signature_header:
        return False

    try:
        # Get raw body
        body = await request.body()
        
        # Extract just the hash part (remove "sha256=")
        if signature_header.startswith("sha256="):
            signature = signature_header[7:]  # Remove 'sha256=' prefix
        else:
            signature = signature_header
        
        # Create expected signature
        expected_signature = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)

    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error verifying WhatsApp signature: {e}")
        return False