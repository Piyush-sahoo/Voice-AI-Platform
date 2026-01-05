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
    """Add a new phone number and cache it."""
    if not request.number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone must be E.164 format")
    
    db = get_database()
    
    phone = {
        "phone_id": f"ph_{uuid.uuid4().hex[:12]}",
        "number": request.number,
        "label": request.label,
        "provider": request.provider,
        "is_active": True,
        "workspace_id": x_workspace_id,  # Multi-tenancy
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.phone_numbers.insert_one(phone)
    await RedisCache.cache_phone(phone["phone_id"], phone)
    
    logger.info(f"Added phone: {phone['phone_id']} (workspace: {x_workspace_id})")
    return {"phone_id": phone["phone_id"], "number": phone["number"], "message": "Added"}


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
    """Delete phone and remove from cache."""
    db = get_database()
    
    result = await db.phone_numbers.delete_one({"phone_id": phone_id})
    
    if result.deleted_count > 0:
        await RedisCache.delete(RedisCache.phone_key(phone_id))
        return {"message": "Deleted"}
    
    raise HTTPException(status_code=404, detail="Phone not found")
