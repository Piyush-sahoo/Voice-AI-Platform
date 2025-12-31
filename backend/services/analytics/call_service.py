"""
Call service for managing call records and triggering calls.
"""
import logging
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from livekit import api

from shared.database.models import CallRecord, CallStatus, CreateCallRequest
from shared.database.connection import get_database
from shared.settings import config
from shared.cache import SessionCache

logger = logging.getLogger("call_service")


class CallService:
    """Service for managing outbound calls."""
    
    @staticmethod
    def generate_call_id(phone_number: str) -> str:
        """Generate a unique call ID."""
        phone_clean = phone_number.replace("+", "")
        random_suffix = random.randint(1000, 9999)
        return f"call-{phone_clean}-{random_suffix}"
    
    @staticmethod
    async def create_call(request: CreateCallRequest, workspace_id: Optional[str] = None) -> CallRecord:
        """
        Create a new call record and dispatch the agent.
        
        Args:
            request: Call creation request with phone number and options
            workspace_id: Workspace ID for multi-tenancy
            
        Returns:
            Created CallRecord
        """
        db = get_database()
        
        # Generate call ID
        call_id = CallService.generate_call_id(request.phone_number)
        room_name = call_id
        
        # Get assistant config if provided
        assistant_config = None
        if request.assistant_id:
            from services.config.assistant_service import AssistantService
            assistant_config = await AssistantService.get_assistant_for_call(request.assistant_id)
        
        # Get SIP config
        sip_trunk_id = config.OUTBOUND_TRUNK_ID  # Default
        sip_id = request.sip_id
        if request.sip_id:
            from services.config.phone_sip_service import SipConfigService
            sip_config = await SipConfigService.get_sip_config(request.sip_id)
            if sip_config:
                sip_trunk_id = sip_config.trunk_id
        elif not request.sip_id:
            # Try to get default SIP config
            from services.config.phone_sip_service import SipConfigService
            default_sip = await SipConfigService.get_default_sip_config()
            if default_sip:
                sip_trunk_id = default_sip.trunk_id
                sip_id = default_sip.sip_id
        
        # Determine final instructions and webhook
        instructions = request.instructions
        webhook_url = request.webhook_url
        
        if assistant_config:
            if not instructions:
                instructions = assistant_config.get("instructions")
            if not webhook_url:
                webhook_url = assistant_config.get("webhook_url")
        
        # Create call record
        call = CallRecord(
            call_id=call_id,
            workspace_id=workspace_id,  # Multi-tenancy
            phone_number=request.phone_number,
            from_number=request.from_number,
            room_name=room_name,
            status=CallStatus.INITIATED,
            assistant_id=request.assistant_id,
            sip_id=sip_id,
            instructions=instructions,
            webhook_url=webhook_url,
            metadata=request.metadata,
            created_at=datetime.now(timezone.utc),
        )
        
        # Save to database
        await db.calls.insert_one(call.to_dict())
        logger.info(f"Created call record: {call_id}")
        
        # Invalidate calls cache
        if workspace_id:
            await SessionCache.invalidate_calls(workspace_id)
        
        # Dispatch the agent
        await CallService._dispatch_agent(call, assistant_config, sip_trunk_id)
        
        return call
    
    @staticmethod
    async def _dispatch_agent(call: CallRecord, assistant_config: dict = None, sip_trunk_id: str = None):
        """Dispatch the LiveKit agent to handle the call."""
        import json
        
        lk_api = api.LiveKitAPI(
            url=config.LIVEKIT_URL,
            api_key=config.LIVEKIT_API_KEY,
            api_secret=config.LIVEKIT_API_SECRET,
        )
        
        try:
            # Build metadata with call config
            metadata_dict = {
                "phone_number": call.phone_number,
                "call_id": call.call_id,
                "assistant_id": call.assistant_id,
                "sip_trunk_id": sip_trunk_id or config.OUTBOUND_TRUNK_ID,
                "instructions": call.instructions,
                "webhook_url": call.webhook_url,
            }
            
            # Add assistant-specific config
            if assistant_config:
                metadata_dict["first_message"] = assistant_config.get("first_message")
                metadata_dict["temperature"] = assistant_config.get("temperature", 0.8)
                
                # Pass full voice_config for user-selectable models
                voice = assistant_config.get("voice", {})
                if voice:
                    # Convert voice config to dict if it's a model
                    if hasattr(voice, "model_dump"):
                        voice_config = voice.model_dump()
                    else:
                        voice_config = voice if isinstance(voice, dict) else {}
                    
                    metadata_dict["voice_config"] = voice_config
                    # Legacy fallback
                    metadata_dict["voice_id"] = voice_config.get("voice_id", "alloy")
                else:
                    metadata_dict["voice_id"] = "alloy"
            
            metadata = json.dumps(metadata_dict)
            
            dispatch_request = api.CreateAgentDispatchRequest(
                agent_name="outbound-caller",
                room=call.room_name,
                metadata=metadata,
            )
            
            dispatch = await lk_api.agent_dispatch.create_dispatch(dispatch_request)
            dispatch_id = getattr(dispatch, 'dispatch_id', None) or getattr(dispatch, 'id', 'unknown')
            logger.info(f"Agent dispatched: {dispatch_id} for call {call.call_id}")
            
        finally:
            await lk_api.aclose()
    
    @staticmethod
    async def get_call(call_id: str, workspace_id: Optional[str] = None) -> Optional[CallRecord]:
        """Get a call record by ID, optionally filtered by workspace (with legacy support)."""
        # Check cache first
        cached = await SessionCache.get_call(call_id)
        if cached:
            return CallRecord.from_dict(cached)
        
        db = get_database()
        query = {"call_id": call_id}
        if workspace_id:
            # Include legacy calls without workspace_id
            query["$or"] = [
                {"workspace_id": workspace_id},
                {"workspace_id": None},
                {"workspace_id": {"$exists": False}},
            ]
        doc = await db.calls.find_one(query)
        if doc:
            # Cache the result
            await SessionCache.cache_call(call_id, doc)
            return CallRecord.from_dict(doc)
        return None
    
    @staticmethod
    async def update_call(call_id: str, updates: Dict[str, Any]) -> Optional[CallRecord]:
        """Update a call record."""
        db = get_database()
        
        result = await db.calls.find_one_and_update(
            {"call_id": call_id},
            {"$set": updates},
            return_document=True,
        )
        
        if result:
            # Invalidate call cache
            await SessionCache.delete(f"call:{call_id}")
            return CallRecord.from_dict(result)
        return None
    
    @staticmethod
    async def list_calls(
        status: Optional[CallStatus] = None,
        phone_number: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        workspace_id: Optional[str] = None,
    ) -> List[CallRecord]:
        """List calls with optional filters, scoped by workspace (with legacy support)."""
        # Check cache first (only for default query without filters)
        if workspace_id and status is None and phone_number is None and skip == 0:
            cached = await SessionCache.get_recent_calls(workspace_id)
            if cached:
                return [CallRecord.from_dict(c) for c in cached[:limit]]
        
        db = get_database()
        
        # Build query with workspace filter (backwards compatible)
        query = {}
        if workspace_id:
            # Include legacy calls without workspace_id
            query["$or"] = [
                {"workspace_id": workspace_id},
                {"workspace_id": None},
                {"workspace_id": {"$exists": False}},
            ]
        if status:
            query["status"] = status.value
        if phone_number:
            query["phone_number"] = phone_number
        
        # Execute query
        cursor = db.calls.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        calls = []
        docs = []
        async for doc in cursor:
            if "_id" in doc:
                del doc["_id"]
            docs.append(doc)
            calls.append(CallRecord.from_dict(doc))
        
        # Cache the result (only for default query)
        if workspace_id and status is None and phone_number is None and skip == 0 and docs:
            await SessionCache.cache_recent_calls(workspace_id, docs)
        
        return calls
    
    @staticmethod
    async def mark_call_answered(call_id: str) -> Optional[CallRecord]:
        """Mark a call as answered."""
        return await CallService.update_call(call_id, {
            "status": CallStatus.ANSWERED.value,
            "answered_at": datetime.utcnow(),
        })
    
    @staticmethod
    async def mark_call_completed(
        call_id: str,
        transcript: List[Dict] = None,
        transcript_url: str = None,
        recording_url: str = None,
    ) -> Optional[CallRecord]:
        """Mark a call as completed with transcript and recording info."""
        ended_at = datetime.utcnow()
        
        # Get current call to calculate duration
        call = await CallService.get_call(call_id)
        duration = 0
        if call and call.answered_at:
            duration = int((ended_at - call.answered_at).total_seconds())
        
        updates = {
            "status": CallStatus.COMPLETED.value,
            "ended_at": ended_at,
            "duration_seconds": duration,
        }
        
        if transcript:
            updates["transcript"] = transcript
        if transcript_url:
            updates["transcript_url"] = transcript_url
        if recording_url:
            updates["recording_url"] = recording_url
        
        return await CallService.update_call(call_id, updates)
    
    @staticmethod
    async def mark_call_failed(call_id: str, reason: str = None) -> Optional[CallRecord]:
        """Mark a call as failed."""
        updates = {
            "status": CallStatus.FAILED.value,
            "ended_at": datetime.utcnow(),
        }
        if reason:
            updates["metadata.failure_reason"] = reason
        
        return await CallService.update_call(call_id, updates)
