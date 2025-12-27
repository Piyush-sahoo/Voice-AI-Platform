"""
Webhook service for sending call event notifications.
"""
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from database.models import CallRecord
from database.connection import get_database

logger = logging.getLogger("webhook_service")


class WebhookService:
    """Service for dispatching webhook notifications."""
    
    # Event types
    CALL_INITIATED = "call.initiated"
    CALL_ANSWERED = "call.answered"
    CALL_COMPLETED = "call.completed"
    CALL_FAILED = "call.failed"
    
    @staticmethod
    async def send_webhook(
        call: CallRecord,
        event: str,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a webhook notification for a call event.
        
        Args:
            call: The call record
            event: Event type (e.g., "call.completed")
            extra_data: Additional data to include in payload
            
        Returns:
            True if webhook was sent successfully
        """
        if not call.webhook_url:
            logger.debug(f"No webhook URL for call {call.call_id}")
            return False
        
        # Build payload
        payload = {
            "event": event,
            "call_id": call.call_id,
            "phone_number": call.phone_number,
            "status": call.status.value if hasattr(call.status, 'value') else call.status,
            "duration_seconds": call.duration_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Add analysis if available
        if call.analysis:
            payload["analysis"] = {
                "success": call.analysis.success,
                "sentiment": call.analysis.sentiment,
                "summary": call.analysis.summary,
                "key_topics": call.analysis.key_topics,
                "action_items": call.analysis.action_items,
            }
        
        # Add extra data
        if extra_data:
            payload.update(extra_data)
        
        # Add custom metadata
        if call.metadata:
            payload["metadata"] = call.metadata
        
        try:
            logger.info(f"Sending webhook to {call.webhook_url} for event {event}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    call.webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Vobiz-Event": event,
                    },
                )
                
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"Webhook sent successfully: {response.status_code}")
                    
                    # Mark webhook as sent in database
                    await WebhookService._mark_webhook_sent(call.call_id)
                    return True
                else:
                    logger.warning(f"Webhook failed: {response.status_code} - {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"Webhook timeout for call {call.call_id}")
            return False
        except Exception as e:
            logger.error(f"Webhook error for call {call.call_id}: {e}")
            return False
    
    @staticmethod
    async def _mark_webhook_sent(call_id: str):
        """Mark the webhook as sent in the database."""
        db = get_database()
        await db.calls.update_one(
            {"call_id": call_id},
            {"$set": {"webhook_sent": True}},
        )
    
    @staticmethod
    async def send_initiated(call: CallRecord) -> bool:
        """Send call.initiated webhook."""
        return await WebhookService.send_webhook(call, WebhookService.CALL_INITIATED)
    
    @staticmethod
    async def send_answered(call: CallRecord) -> bool:
        """Send call.answered webhook."""
        return await WebhookService.send_webhook(call, WebhookService.CALL_ANSWERED)
    
    @staticmethod
    async def send_completed(call: CallRecord) -> bool:
        """Send call.completed webhook."""
        return await WebhookService.send_webhook(call, WebhookService.CALL_COMPLETED)
    
    @staticmethod
    async def send_failed(call: CallRecord, reason: str = None) -> bool:
        """Send call.failed webhook."""
        extra = {"failure_reason": reason} if reason else None
        return await WebhookService.send_webhook(
            call, 
            WebhookService.CALL_FAILED, 
            extra_data=extra,
        )
