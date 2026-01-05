"""SIP Configs router for Configuration Service."""
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
import uuid

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.connection import get_database
from config.cache.redis_cache import RedisCache

logger = logging.getLogger("config-service.sip")
router = APIRouter()


class CreateSipConfigRequest(BaseModel):
    name: str
    sip_domain: str
    sip_username: str
    sip_password: str
    from_number: str
    trunk_id: Optional[str] = None
    description: Optional[str] = None
    is_default: bool = False


class UpdateSipConfigRequest(BaseModel):
    name: Optional[str] = None
    sip_domain: Optional[str] = None
    sip_username: Optional[str] = None
    sip_password: Optional[str] = None
    from_number: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


@router.post("")
async def create_sip_config(
    request: CreateSipConfigRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """Create SIP config and cache it."""
    from config.phone_sip_service import SipConfigService
    
    try:
        sip = await SipConfigService.create_sip_config(request, x_workspace_id)
        return {"sip_id": sip.sip_id, "name": sip.name, "message": "Created"}
    except Exception as e:
        logger.error(f"Error creating SIP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_sip_configs(
    is_active: Optional[bool] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """List all SIP configs for workspace."""
    db = get_database()
    
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    # Multi-tenancy filtering
    if x_workspace_id:
        query["$or"] = [
            {"workspace_id": x_workspace_id},
            {"workspace_id": None},  # Legacy data
            {"workspace_id": {"$exists": False}},
        ]
    
    cursor = db.sip_configs.find(query).sort("created_at", -1)
    
    configs = []
    async for doc in cursor:
        doc.pop("_id", None)
        configs.append(doc)
    
    return {"sip_configs": configs, "count": len(configs)}


@router.get("/default")
async def get_default_sip():
    """Get default SIP config."""
    db = get_database()
    doc = await db.sip_configs.find_one({"is_default": True, "is_active": True})
    
    if not doc:
        raise HTTPException(status_code=404, detail="No default SIP config")
    
    doc.pop("_id", None)
    return doc


@router.get("/{sip_id}")
async def get_sip_config(sip_id: str):
    """Get SIP config by ID (from cache first)."""
    cached = await RedisCache.get_sip(sip_id)
    if cached:
        return cached
    
    db = get_database()
    doc = await db.sip_configs.find_one({"sip_id": sip_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="SIP config not found")
    
    doc.pop("_id", None)
    await RedisCache.cache_sip(sip_id, doc)
    
    return doc


@router.patch("/{sip_id}")
async def update_sip_config(sip_id: str, request: UpdateSipConfigRequest):
    """Update SIP config and refresh cache."""
    db = get_database()
    
    updates = {k: v for k, v in request.model_dump(exclude_unset=True).items() if v is not None}
    
    if updates.get("is_default"):
        await db.sip_configs.update_many({}, {"$set": {"is_default": False}})
    
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.sip_configs.find_one_and_update(
            {"sip_id": sip_id},
            {"$set": updates},
            return_document=True,
        )
        
        if result:
            result.pop("_id", None)
            await RedisCache.cache_sip(sip_id, result)
            return {"sip_id": sip_id, "message": "Updated"}
    
    raise HTTPException(status_code=404, detail="SIP config not found")


@router.delete("/{sip_id}")
async def delete_sip_config(sip_id: str):
    """Delete SIP config and remove from cache."""
    from config.phone_sip_service import SipConfigService
    
    try:
        success = await SipConfigService.delete_sip_config(sip_id)
        if success:
            return {"message": "Deleted"}
        raise HTTPException(status_code=404, detail="SIP config not found")
    except Exception as e:
        logger.error(f"Error deleting SIP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
