"""SIP Configurations API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import CreateSipConfigRequest, UpdateSipConfigRequest
from services import SipConfigService
from shared.auth.dependencies import get_current_user
from shared.auth.models import User

logger = logging.getLogger("api.sip_configs")
router = APIRouter()


@router.post("/sip-configs")
async def create_sip_config(
    request: CreateSipConfigRequest,
    user: User = Depends(get_current_user)
):
    """Create a new SIP configuration for the current user's workspace."""
    try:
        sip = await SipConfigService.create_sip_config(request, user.workspace_id)
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
async def list_sip_configs(
    is_active: Optional[bool] = Query(None),
    user: User = Depends(get_current_user)
):
    """List SIP configurations for the current user's workspace."""
    configs = await SipConfigService.list_sip_configs(
        workspace_id=user.workspace_id,
        is_active=is_active
    )
    return {
        "sip_configs": [c.to_dict() for c in configs],
        "count": len(configs),
    }


@router.get("/sip-configs/{sip_id}")
async def get_sip_config(
    sip_id: str,
    user: User = Depends(get_current_user)
):
    """Get a specific SIP configuration within the user's workspace."""
    sip = await SipConfigService.get_sip_config(sip_id, user.workspace_id)
    if not sip:
        raise HTTPException(status_code=404, detail="SIP config not found")
    return sip.to_dict()


@router.patch("/sip-configs/{sip_id}")
async def update_sip_config(
    sip_id: str,
    request: UpdateSipConfigRequest,
    user: User = Depends(get_current_user)
):
    """Update a SIP configuration within the user's workspace."""
    sip = await SipConfigService.update_sip_config(sip_id, request, user.workspace_id)
    if not sip:
        raise HTTPException(status_code=404, detail="SIP config not found")
    return {
        "sip_id": sip.sip_id,
        "name": sip.name,
        "message": "SIP config updated successfully",
    }


@router.delete("/sip-configs/{sip_id}")
async def delete_sip_config(
    sip_id: str,
    user: User = Depends(get_current_user)
):
    """Delete a SIP configuration within the user's workspace."""
    deleted = await SipConfigService.delete_sip_config(sip_id, user.workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SIP config not found")
    return {"message": "SIP config deleted successfully"}
