"""
Celery tasks for campaign execution.
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from celery import group
from .celery_app import celery_app

logger = logging.getLogger("queue.tasks")


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
)
def make_single_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single outbound call.
    
    Args:
        call_data: Dictionary containing:
            - phone_number: Target phone number
            - assistant_id: Which assistant to use
            - campaign_id: Parent campaign ID
            - contact_index: Index in contacts list
            
    Returns:
        Call result with status
    """
    from services.call_service import CallService
    from database.models import CreateCallRequest
    
    phone_number = call_data.get("phone_number")
    assistant_id = call_data.get("assistant_id")
    campaign_id = call_data.get("campaign_id")
    contact_index = call_data.get("contact_index", 0)
    
    logger.info(f"[Task {self.request.id}] Making call to {phone_number}")
    
    try:
        # Create call request
        request = CreateCallRequest(
            phone_number=phone_number,
            assistant_id=assistant_id,
            metadata={"campaign_id": campaign_id, "contact_index": contact_index}
        )
        
        # Create call (async)
        async def create_call():
            return await CallService.create_call(request)
        
        call = run_async(create_call())
        
        logger.info(f"[Task {self.request.id}] Call created: {call.call_id}")
        
        return {
            "success": True,
            "call_id": call.call_id,
            "phone_number": phone_number,
            "status": call.status.value,
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Call failed: {e}")
        
        if self.request.retries >= self.max_retries:
            # Max retries reached, mark as failed
            return {
                "success": False,
                "phone_number": phone_number,
                "error": str(e),
            }
        
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def execute_campaign(self, campaign_id: str) -> Dict[str, Any]:
    """
    Execute a campaign by processing contacts in batches.
    
    Args:
        campaign_id: Campaign to execute
        
    Returns:
        Campaign execution result
    """
    from database.connection import connect_to_database
    from config import config
    
    logger.info(f"[Campaign {campaign_id}] Starting execution")
    
    async def run_campaign():
        # Connect to database
        await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
        
        from services.campaign_service import CampaignService
        
        # Get campaign
        campaign = await CampaignService.get_campaign(campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return {"success": False, "error": "Campaign not found"}
        
        # Get pending contacts
        pending_contacts = [
            (i, c) for i, c in enumerate(campaign.contacts)
            if c.status == "pending"
        ]
        
        if not pending_contacts:
            logger.info(f"[Campaign {campaign_id}] No pending contacts")
            return {"success": True, "message": "No pending contacts"}
        
        max_concurrent = campaign.max_concurrent_calls or 2
        logger.info(f"[Campaign {campaign_id}] Processing {len(pending_contacts)} contacts, max concurrent: {max_concurrent}")
        
        # Process in batches
        batch_results = []
        for batch_start in range(0, len(pending_contacts), max_concurrent):
            batch = pending_contacts[batch_start:batch_start + max_concurrent]
            
            # Create tasks for this batch
            tasks = []
            for contact_index, contact in batch:
                call_data = {
                    "phone_number": contact.phone_number,
                    "assistant_id": campaign.assistant_id,
                    "campaign_id": campaign_id,
                    "contact_index": contact_index,
                }
                tasks.append(make_single_call.s(call_data))
            
            # Execute batch in parallel
            job = group(tasks)
            result = job.apply_async()
            
            # Wait for batch to complete
            batch_result = result.get(timeout=600)  # 10 min timeout per batch
            batch_results.extend(batch_result)
            
            logger.info(f"[Campaign {campaign_id}] Batch completed: {len(batch_result)} calls")
        
        # Mark campaign as completed
        from database.connection import get_database
        db = get_database()
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "total_calls": len(batch_results),
            "successful": sum(1 for r in batch_results if r.get("success")),
            "failed": sum(1 for r in batch_results if not r.get("success")),
        }
    
    try:
        result = run_async(run_campaign())
        logger.info(f"[Campaign {campaign_id}] Execution complete: {result}")
        return result
    except Exception as e:
        logger.error(f"[Campaign {campaign_id}] Execution failed: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task
def health_check() -> Dict[str, Any]:
    """Simple health check task for testing Celery connectivity."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
