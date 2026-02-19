"""
Assistant service for managing AI assistants.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from shared.database.models import (
    Assistant, 
    CreateAssistantRequest,
    UpdateAssistantRequest,
)
from shared.database.connection import get_database
from shared.cache import SessionCache

logger = logging.getLogger("assistant_service")


class AssistantService:
    """Service for managing assistants."""
    
    @staticmethod
    async def create_assistant(request: CreateAssistantRequest, workspace_id: str = None) -> Assistant:
        """Create a new assistant."""
        db = get_database()
        
        assistant = Assistant(
            workspace_id=workspace_id,
            name=request.name,
            description=request.description,
            instructions=request.instructions,
            first_message=request.first_message,
            voice=request.voice or Assistant.model_fields['voice'].default_factory(),
            temperature=request.temperature,
            webhook_url=request.webhook_url,
        )
        
        await db.assistants.insert_one(assistant.to_dict())
        logger.info(f"Created assistant: {assistant.assistant_id} - {assistant.name}")
        
        # Invalidate assistants list cache
        if workspace_id:
            await SessionCache.invalidate_assistants(workspace_id)
        
        return assistant
    
    @staticmethod
    async def get_assistant(assistant_id: str, workspace_id: str = None) -> Optional[Assistant]:
        """Get an assistant by ID."""
        # Check cache first
        cached = await SessionCache.get_assistant(assistant_id)
        if cached:
            return Assistant.from_dict(cached)
        
        db = get_database()
        query = {"assistant_id": assistant_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        doc = await db.assistants.find_one(query)
        if doc:
            # Cache the result
            await SessionCache.cache_assistant(assistant_id, doc)
            return Assistant.from_dict(doc)
        return None
    
    @staticmethod
    async def list_assistants(
        workspace_id: str = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Assistant]:
        """List assistants with optional filters."""
        # Check cache first (only for default query without pagination)
        if workspace_id and is_active is None and skip == 0 and limit >= 50:
            cached = await SessionCache.get_assistants(workspace_id)
            if cached:
                return [Assistant.from_dict(a) for a in cached[:limit]]
        
        db = get_database()
        
        query = {}
        if workspace_id:
            query["workspace_id"] = workspace_id
        if is_active is not None:
            query["is_active"] = is_active
        
        cursor = db.assistants.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        assistants = []
        docs = []
        async for doc in cursor:
            if "_id" in doc:
                del doc["_id"]
            docs.append(doc)
            assistants.append(Assistant.from_dict(doc))
        
        # Cache the result (only for default query)
        if workspace_id and is_active is None and skip == 0 and docs:
            await SessionCache.cache_assistants(workspace_id, docs)
        
        return assistants
    
    @staticmethod
    async def update_assistant(
        assistant_id: str, 
        request: UpdateAssistantRequest,
        workspace_id: str = None
    ) -> Optional[Assistant]:
        """Update an assistant, scoped by workspace."""
        db = get_database()
        
        # Build query with workspace filter
        query = {"assistant_id": assistant_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        
        # Build update dict with only provided fields
        updates = {}
        update_data = request.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            if value is not None:
                if key == "voice" and isinstance(value, dict):
                    updates["voice"] = value
                else:
                    updates[key] = value
        
        if updates:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await db.assistants.find_one_and_update(
                query,
                {"$set": updates},
                return_document=True,
            )
            
            if result:
                logger.info(f"Updated assistant: {assistant_id}")
                # Invalidate cache
                await SessionCache.invalidate_assistant(assistant_id, workspace_id)
                return Assistant.from_dict(result)
        
        return None
    
    @staticmethod
    async def delete_assistant(assistant_id: str, workspace_id: str = None) -> bool:
        """Delete an assistant, scoped by workspace."""
        db = get_database()
        query = {"assistant_id": assistant_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        result = await db.assistants.delete_one(query)
        
        if result.deleted_count > 0:
            logger.info(f"Deleted assistant: {assistant_id}")
            # Invalidate cache
            await SessionCache.invalidate_assistant(assistant_id, workspace_id)
            return True
        return False
    
    @staticmethod
    async def get_assistant_for_call(assistant_id: str) -> Optional[Dict[str, Any]]:
        """Get assistant config optimized for call handling."""
        assistant = await AssistantService.get_assistant(assistant_id)
        if not assistant or not assistant.is_active:
            return None
        
        logger.info(f"Assistant data: {assistant}")

        return {
            "instructions": assistant.instructions,
            "first_message": assistant.first_message,
            "voice": assistant.voice.model_dump() if assistant.voice else {},
            "temperature": assistant.temperature,
            "webhook_url": assistant.webhook_url,
            "tools": [t.model_dump() for t in assistant.tools] if assistant.tools else [],
        }

