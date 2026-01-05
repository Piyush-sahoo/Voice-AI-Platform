"""Phone Numbers router for Configuration Service."""
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

logger = logging.getLogger("config-service.phones")
router = APIRouter()


class CreatePhoneNumberRequest(BaseModel):
    number: str
    label: Optional[str] = None
    provider: str = "default"


@router.post("")
async def add_phone_number(
    request: CreatePhoneNumberRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """Add a new inbound phone number and configure LiveKit."""
    if not request.number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone must be E.164 format")
    
    from config.phone_sip_service import PhoneNumberService
    from shared.database.models import CreateInboundNumberRequest
    
    try:
        # Map simple request to full inbound request
        inbound_req = CreateInboundNumberRequest(
            number=request.number,
            label=request.label,
            provider=request.provider,
            # Default optional fields
            assistant_id=None,
            allowed_addresses=[],
            krisp_enabled=True 
        )
        
        phone = await PhoneNumberService.create_inbound_number(inbound_req, x_workspace_id)
        
        # Include sip_uri in response so frontend can show it
        return {
            "phone_id": phone.phone_id, 
            "number": phone.number, 
            "sip_uri": phone.sip_uri,
            "message": "Added and configured in LiveKit"
        }
    except Exception as e:
        logger.error(f"Error adding phone number: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_phone_numbers(
    is_active: Optional[bool] = Query(None),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """List all phone numbers for workspace."""
    db = get_database()
    
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    # Multi-tenancy filtering
    if x_workspace_id:
        query["$or"] = [
            {"workspace_id": x_workspace_id},
            {"workspace_id": None},
            {"workspace_id": {"$exists": False}},
        ]
    
    cursor = db.phone_numbers.find(query).sort("created_at", -1)
    
    phones = []
    async for doc in cursor:
        doc.pop("_id", None)
        phones.append(doc)
    
    return {"phone_numbers": phones, "count": len(phones)}


@router.get("/{phone_id}")
async def get_phone_number(phone_id: str):
    """Get phone by ID (from cache first)."""
    cached = await RedisCache.get_phone(phone_id)
    if cached:
        return cached
    
    db = get_database()
    doc = await db.phone_numbers.find_one({"phone_id": phone_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Phone not found")
    
    doc.pop("_id", None)
    await RedisCache.cache_phone(phone_id, doc)
    
    return doc


@router.delete("/{phone_id}")
async def delete_phone_number(phone_id: str):
    """Delete phone/inbound number and clean up LiveKit resources."""
    from config.phone_sip_service import PhoneNumberService
    
    try:
        # We try to delete as an inbound number first (which handles LiveKit cleanup)
        success = await PhoneNumberService.delete_inbound_number(phone_id)
        
        # If not found or failed, it might be a regular phone number (though in this system most are inbound)
        # But delete_inbound_number handles the DB delete too.
        
        if success:
            return {"message": "Deleted"}
            
        # Fallback check if it was just deleted? Or verify existance?
        # delete_inbound_number returns False if not found.
        raise HTTPException(status_code=404, detail="Phone not found")

    except Exception as e:
        logger.error(f"Error deleting phone number: {e}")
        raise HTTPException(status_code=500, detail=str(e))
