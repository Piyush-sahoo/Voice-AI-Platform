"""Assistants router for Configuration Service."""
import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Depends, Header
from pydantic import BaseModel, Field
import uuid

# Add parent to path for shared imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.connection import get_database
from config.cache.redis_cache import RedisCache

logger = logging.getLogger("config-service.assistants")
router = APIRouter()


# ============== Models ==============

class VoiceConfig(BaseModel):
    provider: str = "openai"
    voice_id: str = "alloy"


class CreateAssistantRequest(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: str = "You are a helpful voice assistant."
    first_message: Optional[str] = None
    voice: Optional[VoiceConfig] = None
    temperature: float = 0.8
    webhook_url: Optional[str] = None


class UpdateAssistantRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    first_message: Optional[str] = None
    voice: Optional[VoiceConfig] = None
    temperature: Optional[float] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None


# ============== Endpoints ==============

@router.post("")
async def create_assistant(
    request: CreateAssistantRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """Create a new AI assistant and cache it."""
    db = get_database()
    
    assistant = {
        "assistant_id": f"asst_{uuid.uuid4().hex[:12]}",
        "name": request.name,
        "description": request.description,
        "instructions": request.instructions,
        "first_message": request.first_message,
        "voice": request.voice.model_dump() if request.voice else {"provider": "openai", "voice_id": "alloy"},
        "temperature": request.temperature,
        "webhook_url": request.webhook_url,
        "is_active": True,
        "workspace_id": x_workspace_id,  # Multi-tenancy
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.assistants.insert_one(assistant)
    
    # Cache immediately
    await RedisCache.cache_assistant(assistant["assistant_id"], assistant)
    
    logger.info(f"Created assistant: {assistant['assistant_id']} (workspace: {x_workspace_id})")
    return {"assistant_id": assistant["assistant_id"], "name": assistant["name"], "message": "Created"}


@router.get("")
async def list_assistants(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """List all assistants for workspace."""
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
    
    cursor = db.assistants.find(query).sort("created_at", -1).skip(skip).limit(limit)
    
    assistants = []
    async for doc in cursor:
        doc.pop("_id", None)
        assistants.append(doc)
    
    return {"assistants": assistants, "count": len(assistants)}


@router.get("/{assistant_id}")
async def get_assistant(assistant_id: str):
    """Get assistant by ID (from cache first)."""
    # Try cache first
    cached = await RedisCache.get_assistant(assistant_id)
    if cached:
        logger.debug(f"Cache hit: {assistant_id}")
        return cached
    
    # Fallback to DB
    db = get_database()
    doc = await db.assistants.find_one({"assistant_id": assistant_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    doc.pop("_id", None)
    
    # Cache for next time
    await RedisCache.cache_assistant(assistant_id, doc)
    
    return doc


@router.patch("/{assistant_id}")
async def update_assistant(assistant_id: str, request: UpdateAssistantRequest):
    """Update assistant and invalidate cache."""
    db = get_database()
    
    updates = {}
    for key, value in request.model_dump(exclude_unset=True).items():
        if value is not None:
            if key == "voice" and isinstance(value, dict):
                updates["voice"] = value
            else:
                updates[key] = value
    
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.assistants.find_one_and_update(
            {"assistant_id": assistant_id},
            {"$set": updates},
            return_document=True,
        )
        
        if result:
            result.pop("_id", None)
            # Update cache
            await RedisCache.cache_assistant(assistant_id, result)
            return {"assistant_id": assistant_id, "message": "Updated"}
    
    raise HTTPException(status_code=404, detail="Assistant not found")


@router.delete("/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """Delete assistant and remove from cache."""
    db = get_database()
    
    result = await db.assistants.delete_one({"assistant_id": assistant_id})
    
    if result.deleted_count > 0:
        # Remove from cache
        await RedisCache.delete(RedisCache.assistant_key(assistant_id))
        return {"message": "Deleted"}
    
    raise HTTPException(status_code=404, detail="Assistant not found")
