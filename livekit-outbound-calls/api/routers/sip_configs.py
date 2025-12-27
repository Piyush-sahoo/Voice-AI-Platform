"""SIP Configurations API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from database.models import CreateSipConfigRequest, UpdateSipConfigRequest
from services import SipConfigService
from auth.dependencies import get_current_user
from auth.models import User

logger = logging.getLogger("api.sip_configs")
router = APIRouter()


@router.post("/sip-configs")
async def create_sip_config(request: CreateSipConfigRequest):
    """Create a new SIP configuration."""
    try:
        sip = await SipConfigService.create_sip_config(request)
        return {
            "sip_id": sip.sip_id,
            "name": sip.name,
            "trunk_id": sip.trunk_id,
            "message": "SIP config created successfully",
        }
    except Exception as e:
        logger.error(f"Failed to create SIP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sip-configs")
async def list_sip_configs(is_active: Optional[bool] = Query(None)):
    """List all SIP configurations."""
    configs = await SipConfigService.list_sip_configs(is_active=is_active)
    return {
        "sip_configs": [c.to_dict() for c in configs],
        "count": len(configs),
    }


@router.get("/sip-configs/{sip_id}")
async def get_sip_config(sip_id: str):
    """Get a specific SIP configuration."""
    sip = await SipConfigService.get_sip_config(sip_id)
    if not sip:
        raise HTTPException(status_code=404, detail="SIP config not found")
    return sip.to_dict()


@router.patch("/sip-configs/{sip_id}")
async def update_sip_config(sip_id: str, request: UpdateSipConfigRequest):
    """Update a SIP configuration."""
    sip = await SipConfigService.update_sip_config(sip_id, request)
    if not sip:
        raise HTTPException(status_code=404, detail="SIP config not found")
    return {
        "sip_id": sip.sip_id,
        "name": sip.name,
        "message": "SIP config updated successfully",
    }


@router.delete("/sip-configs/{sip_id}")
async def delete_sip_config(sip_id: str):
    """Delete a SIP configuration."""
    deleted = await SipConfigService.delete_sip_config(sip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SIP config not found")
    return {"message": "SIP config deleted successfully"}
