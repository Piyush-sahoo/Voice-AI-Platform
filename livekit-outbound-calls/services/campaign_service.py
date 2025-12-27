"""
Campaign service for batch calling operations.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from database.models import (
    Campaign,
    CampaignStatus,
    CampaignContact,
    CreateCampaignRequest,
    UpdateCampaignRequest,
    CreateCallRequest,
)
from database.connection import get_database
from services.call_service import CallService

logger = logging.getLogger("campaign_service")


class CampaignService:
    """Service for managing campaigns."""
    
    # Track running campaigns
    _running_campaigns: Dict[str, bool] = {}
    
    @staticmethod
    async def create_campaign(request: CreateCampaignRequest, workspace_id: str = None) -> Campaign:
        """Create a new campaign."""
        db = get_database()
        
        # Convert contacts to CampaignContact objects
        contacts = []
        for c in request.contacts:
            contacts.append(CampaignContact(
                phone_number=c.get("phone_number"),
                name=c.get("name"),
                variables=c.get("variables", {}),
            ))
        
        campaign = Campaign(
            workspace_id=workspace_id,
            name=request.name,
            description=request.description,
            assistant_id=request.assistant_id,
            sip_id=request.sip_id,
            contacts=contacts,
            total_contacts=len(contacts),
            max_concurrent_calls=request.max_concurrent_calls,
            retry_failed=request.retry_failed,
        )
        
        await db.campaigns.insert_one(campaign.to_dict())
        logger.info(f"Created campaign: {campaign.campaign_id} with {len(contacts)} contacts")
        
        return campaign
    
    @staticmethod
    async def get_campaign(campaign_id: str, workspace_id: str = None) -> Optional[Campaign]:
        """Get a campaign by ID."""
        db = get_database()
        query = {"campaign_id": campaign_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        doc = await db.campaigns.find_one(query)
        if doc:
            return Campaign.from_dict(doc)
        return None
    
    @staticmethod
    async def list_campaigns(
        workspace_id: str = None,
        status: Optional[CampaignStatus] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Campaign]:
        """List campaigns with optional filters."""
        db = get_database()
        
        query = {}
        if workspace_id:
            query["workspace_id"] = workspace_id
        if status:
            query["status"] = status.value
        
        cursor = db.campaigns.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        campaigns = []
        async for doc in cursor:
            campaigns.append(Campaign.from_dict(doc))
        
        return campaigns
    
    @staticmethod
    async def start_campaign(campaign_id: str) -> Optional[Campaign]:
        """Start executing a campaign."""
        db = get_database()
        
        # Get campaign
        campaign = await CampaignService.get_campaign(campaign_id)
        if not campaign:
            return None
        
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
            logger.warning(f"Campaign {campaign_id} cannot be started (status: {campaign.status})")
            return None
        
        # Update status
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {
                "status": CampaignStatus.RUNNING.value,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        
        # Start execution in background
        CampaignService._running_campaigns[campaign_id] = True
        asyncio.create_task(CampaignService._execute_campaign(campaign_id))
        
        logger.info(f"Started campaign: {campaign_id}")
        
        # Return updated campaign
        return await CampaignService.get_campaign(campaign_id)
    
    @staticmethod
    async def pause_campaign(campaign_id: str) -> Optional[Campaign]:
        """Pause a running campaign."""
        db = get_database()
        
        # Stop execution
        CampaignService._running_campaigns[campaign_id] = False
        
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {
                "status": CampaignStatus.PAUSED.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        
        logger.info(f"Paused campaign: {campaign_id}")
        return await CampaignService.get_campaign(campaign_id)
    
    @staticmethod
    async def cancel_campaign(campaign_id: str) -> Optional[Campaign]:
        """Cancel a campaign."""
        db = get_database()
        
        # Stop execution
        CampaignService._running_campaigns[campaign_id] = False
        
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {
                "status": CampaignStatus.CANCELLED.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        
        logger.info(f"Cancelled campaign: {campaign_id}")
        return await CampaignService.get_campaign(campaign_id)
    
    @staticmethod
    async def _execute_campaign(campaign_id: str):
        """Execute campaign calls in background."""
        db = get_database()
        
        try:
            campaign = await CampaignService.get_campaign(campaign_id)
            if not campaign:
                return
            
            pending_contacts = [c for c in campaign.contacts if c.status == "pending"]
            semaphore = asyncio.Semaphore(campaign.max_concurrent_calls)
            
            async def make_call(contact: CampaignContact, index: int):
                async with semaphore:
                    # Check if campaign is still running
                    if not CampaignService._running_campaigns.get(campaign_id, False):
                        return
                    
                    try:
                        # Create call request
                        call_request = CreateCallRequest(
                            phone_number=contact.phone_number,
                            assistant_id=campaign.assistant_id,
                            sip_id=campaign.sip_id,
                            metadata={"campaign_id": campaign_id, "contact_name": contact.name},
                        )
                        
                        # Make the call
                        call = await CallService.create_call(call_request)
                        
                        # Update contact status
                        await db.campaigns.update_one(
                            {"campaign_id": campaign_id},
                            {"$set": {
                                f"contacts.{index}.status": "called",
                                f"contacts.{index}.call_id": call.call_id,
                                f"contacts.{index}.called_at": datetime.now(timezone.utc).isoformat(),
                            }}
                        )
                        
                        logger.info(f"Campaign {campaign_id}: Called {contact.phone_number}")
                        
                        # Wait between calls to avoid overwhelming
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Campaign {campaign_id}: Failed to call {contact.phone_number}: {e}")
                        await db.campaigns.update_one(
                            {"campaign_id": campaign_id},
                            {"$set": {
                                f"contacts.{index}.status": "failed",
                                f"contacts.{index}.result": str(e),
                            }}
                        )
            
            # Execute calls
            tasks = []
            for i, contact in enumerate(campaign.contacts):
                if contact.status == "pending":
                    tasks.append(make_call(contact, i))
            
            await asyncio.gather(*tasks)
            
            # Mark campaign as completed
            if CampaignService._running_campaigns.get(campaign_id, False):
                await db.campaigns.update_one(
                    {"campaign_id": campaign_id},
                    {"$set": {
                        "status": CampaignStatus.COMPLETED.value,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }}
                )
                logger.info(f"Campaign {campaign_id} completed")
            
        except Exception as e:
            logger.error(f"Campaign {campaign_id} execution failed: {e}")
            await db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {"$set": {"status": CampaignStatus.PAUSED.value}}
            )
        finally:
            CampaignService._running_campaigns.pop(campaign_id, None)
    
    @staticmethod
    async def get_campaign_stats(campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign statistics."""
        campaign = await CampaignService.get_campaign(campaign_id)
        if not campaign:
            return None
        
        stats = {
            "total": len(campaign.contacts),
            "pending": sum(1 for c in campaign.contacts if c.status == "pending"),
            "called": sum(1 for c in campaign.contacts if c.status == "called"),
            "completed": sum(1 for c in campaign.contacts if c.status == "completed"),
            "failed": sum(1 for c in campaign.contacts if c.status == "failed"),
        }
        
        return stats
