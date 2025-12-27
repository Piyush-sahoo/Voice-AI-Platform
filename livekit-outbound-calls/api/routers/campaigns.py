"""Campaigns API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from database.models import (
    CreateCampaignRequest,
    UpdateCampaignRequest,
    CampaignResponse,
    CampaignStatus,
)
from services import CampaignService
from auth.dependencies import get_current_user
from auth.models import User

logger = logging.getLogger("api.campaigns")
router = APIRouter()


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    request: CreateCampaignRequest,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Create a new campaign for batch calling.
    
    - **name**: Campaign name
    - **assistant_id**: Which assistant to use for calls
    - **contacts**: List of contacts with phone_number, name (optional), variables (optional)
    - **max_concurrent_calls**: How many calls to make simultaneously
    """
    if not request.contacts:
        raise HTTPException(status_code=400, detail="At least one contact is required")
    
    try:
        workspace_id = user.workspace_id if user else None
        campaign = await CampaignService.create_campaign(request, workspace_id=workspace_id)
        
        return CampaignResponse(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            status=campaign.status.value,
            total_contacts=campaign.total_contacts,
            message="Campaign created successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns")
async def list_campaigns(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    user: Optional[User] = Depends(get_current_user)
):
    """List all campaigns."""
    status_enum = None
    if status:
        try:
            status_enum = CampaignStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    workspace_id = user.workspace_id if user else None
    campaigns = await CampaignService.list_campaigns(
        workspace_id=workspace_id,
        status=status_enum,
        limit=limit,
        skip=skip,
    )
    
    return {
        "campaigns": [
            {
                "campaign_id": c.campaign_id,
                "name": c.name,
                "status": c.status.value,
                "total_contacts": c.total_contacts,
                "calls_completed": c.calls_completed,
                "created_at": c.created_at.isoformat(),
            }
            for c in campaigns
        ],
        "count": len(campaigns),
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details."""
    campaign = await CampaignService.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign.to_dict()


@router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics."""
    stats = await CampaignService.get_campaign_stats(campaign_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return stats


@router.post("/campaigns/{campaign_id}/start")
async def start_campaign(campaign_id: str):
    """Start a campaign."""
    campaign = await CampaignService.start_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=400, detail="Campaign not found or cannot be started")
    
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        name=campaign.name,
        status=campaign.status.value,
        total_contacts=campaign.total_contacts,
        message="Campaign started",
    )


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    """Pause a running campaign."""
    campaign = await CampaignService.pause_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        name=campaign.name,
        status=campaign.status.value,
        total_contacts=campaign.total_contacts,
        message="Campaign paused",
    )


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: str):
    """Cancel a campaign."""
    campaign = await CampaignService.cancel_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        name=campaign.name,
        status=campaign.status.value,
        total_contacts=campaign.total_contacts,
        message="Campaign cancelled",
    )


@router.patch("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, request: UpdateCampaignRequest):
    """Update a campaign (only allowed for draft campaigns)."""
    from database.connection import get_database
    from datetime import datetime, timezone
    
    db = get_database()
    
    # Get current campaign
    campaign = await CampaignService.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only update draft campaigns")
    
    updates = {}
    update_data = request.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            updates[key] = value
    
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": updates}
        )
    
    return CampaignResponse(
        campaign_id=campaign_id,
        name=updates.get("name", campaign.name),
        status=campaign.status.value,
        total_contacts=campaign.total_contacts,
        message="Campaign updated successfully",
    )


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign."""
    from database.connection import get_database
    
    db = get_database()
    
    # Only allow deleting draft or cancelled campaigns
    campaign = await CampaignService.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.CANCELLED, CampaignStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Cannot delete active campaigns")
    
    await db.campaigns.delete_one({"campaign_id": campaign_id})
    
    return {"message": "Campaign deleted successfully"}
