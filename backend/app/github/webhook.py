"""
AutoCodit Agent - GitHub Webhook Handler

Handles incoming GitHub App webhook events and routes them to
appropriate processors for task creation and management.
"""

import hashlib
import hmac
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_settings
from app.github.events import process_github_event
from app.schemas.github import WebhookEvent

logger = structlog.get_logger()
router = APIRouter()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature:
        return False
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(signature, expected_signature)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle GitHub webhook events"""
    settings = get_settings()
    
    # Get headers
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not event_type:
        logger.warning("Missing X-GitHub-Event header")
        raise HTTPException(status_code=400, detail="Missing event type")
    
    if not delivery_id:
        logger.warning("Missing X-GitHub-Delivery header")
        raise HTTPException(status_code=400, detail="Missing delivery ID")
    
    # Get request body
    payload = await request.body()
    
    # Verify webhook signature
    if not verify_webhook_signature(payload, signature, settings.GITHUB_WEBHOOK_SECRET):
        logger.warning(
            "Invalid webhook signature",
            event_type=event_type,
            delivery_id=delivery_id
        )
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse payload
    try:
        import json
        payload_data = json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError as e:
        logger.error("Failed to parse webhook payload", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Create webhook event
    webhook_event = WebhookEvent(
        event_type=event_type,
        delivery_id=delivery_id,
        payload=payload_data
    )
    
    logger.info(
        "Received GitHub webhook",
        event_type=event_type,
        delivery_id=delivery_id,
        action=payload_data.get("action"),
        repository=payload_data.get("repository", {}).get("full_name")
    )
    
    # Process event in background
    background_tasks.add_task(
        process_github_event,
        webhook_event
    )
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "received",
            "event_type": event_type,
            "delivery_id": delivery_id
        }
    )


@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint for webhook configuration"""
    return {
        "status": "ok",
        "message": "Webhook endpoint is configured correctly",
        "service": "autocodit-agent"
    }