"""
Phone Number and SIP Config service.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List

from shared.database.models import (
    PhoneNumber,
    SipConfig,
    CreatePhoneNumberRequest,
    CreateInboundNumberRequest,
    CreateSipConfigRequest,
    UpdateSipConfigRequest,
)
from shared.database.connection import get_database
from shared.cache import SessionCache

logger = logging.getLogger("phone_sip_service")


class PhoneNumberService:
    """Service for managing phone numbers."""
    
    @staticmethod
    async def add_phone_number(request: CreatePhoneNumberRequest, workspace_id: str = None) -> PhoneNumber:
        """Add a new phone number."""
        db = get_database()
        
        phone = PhoneNumber(
            workspace_id=workspace_id,
            number=request.number,
            label=request.label,
            provider=request.provider,
        )
        
        await db.phone_numbers.insert_one(phone.to_dict())
        logger.info(f"Added phone number: {phone.phone_id} - {phone.number} (workspace: {workspace_id})")
        
        # Invalidate phones cache
        if workspace_id:
            await SessionCache.invalidate_phones(workspace_id)
        
        return phone
    
    @staticmethod
    async def list_phone_numbers(workspace_id: str = None, is_active: Optional[bool] = None) -> List[PhoneNumber]:
        """List all phone numbers, scoped by workspace."""
        # Check cache first (only for default query)
        if workspace_id and is_active is None:
            cached = await SessionCache.get_phones(workspace_id)
            if cached:
                return [PhoneNumber.from_dict(p) for p in cached]
        
        db = get_database()
        
        query = {}
        if workspace_id:
            query["workspace_id"] = workspace_id
        if is_active is not None:
            query["is_active"] = is_active
        
        cursor = db.phone_numbers.find(query).sort("created_at", -1)
        
        phones = []
        docs = []
        async for doc in cursor:
            if "_id" in doc:
                del doc["_id"]
            docs.append(doc)
            phones.append(PhoneNumber.from_dict(doc))
        
        # Cache the result (only for default query)
        if workspace_id and is_active is None and docs:
            await SessionCache.cache_phones(workspace_id, docs)
        
        return phones
    
    @staticmethod
    async def get_phone_number(phone_id: str, workspace_id: str = None) -> Optional[PhoneNumber]:
        """Get a phone number by ID, scoped by workspace."""
        db = get_database()
        query = {"phone_id": phone_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        doc = await db.phone_numbers.find_one(query)
        if doc:
            return PhoneNumber.from_dict(doc)
        return None
    
    @staticmethod
    async def delete_phone_number(phone_id: str, workspace_id: str = None) -> bool:
        """Delete a phone number, scoped by workspace."""
        db = get_database()
        query = {"phone_id": phone_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        result = await db.phone_numbers.delete_one(query)
        if result.deleted_count > 0:
            # Invalidate phones cache
            if workspace_id:
                await SessionCache.invalidate_phones(workspace_id)
            return True
        return False
    
    @staticmethod
    async def create_inbound_number(request: CreateInboundNumberRequest, workspace_id: str = None) -> PhoneNumber:
        """
        Create an inbound phone number with LiveKit trunk and dispatch rule.
        This enables automatic agent dispatch for incoming calls.
        """
        from livekit import api
        from livekit.protocol import sip as sip_proto
        from shared.settings import config
        
        db = get_database()
        
        # Connect to LiveKit API
        lk_api = api.LiveKitAPI(
            url=config.LIVEKIT_URL,
            api_key=config.LIVEKIT_API_KEY,
            api_secret=config.LIVEKIT_API_SECRET,
        )
        
        try:
            # 1. Create Inbound Trunk
            logger.info(f"Creating inbound trunk for {request.number}")
            trunk = await lk_api.sip.create_sip_inbound_trunk(
                api.CreateSIPInboundTrunkRequest(
                    trunk=api.SIPInboundTrunkInfo(
                        name=f"Inbound-{request.number}",
                        numbers=[request.number],
                        allowed_addresses=request.allowed_addresses,
                        krisp_enabled=request.krisp_enabled,
                    )
                )
            )
            trunk_id = trunk.sip_trunk_id
            logger.info(f"Created inbound trunk: {trunk_id}")
            
            # 2. Create Dispatch Rule linking to agent
            logger.info(f"Creating dispatch rule for agent")
            dispatch_rule = sip_proto.SIPDispatchRuleInfo(
                name=f"Dispatch-{request.number}",
                trunk_ids=[trunk_id],
                rule=sip_proto.SIPDispatchRule(
                    dispatch_rule_individual=sip_proto.SIPDispatchRuleIndividual(
                        room_prefix="call-",
                    )
                ),
            )
            # Set room config with agent dispatch
            dispatch_rule.room_config.CopyFrom(
                api.RoomConfiguration(
                    agents=[api.RoomAgentDispatch(agent_name="voice-assistant")]
                )
            )
            
            result = await lk_api.sip.create_sip_dispatch_rule(
                api.CreateSIPDispatchRuleRequest(dispatch_rule=dispatch_rule)
            )
            dispatch_rule_id = result.sip_dispatch_rule_id
            logger.info(f"Created dispatch rule: {dispatch_rule_id}")
            
            # 3. Save to database
            phone = PhoneNumber(
                workspace_id=workspace_id,
                number=request.number,
                label=request.label,
                provider=request.provider,
                direction="inbound",
                assistant_id=request.assistant_id,
                inbound_trunk_id=trunk_id,
                dispatch_rule_id=dispatch_rule_id,
                allowed_addresses=request.allowed_addresses,
                krisp_enabled=request.krisp_enabled,
            )
            
            await db.phone_numbers.insert_one(phone.to_dict())
            logger.info(f"Inbound number saved: {phone.phone_id}")
            
            # Invalidate cache
            if workspace_id:
                await SessionCache.invalidate_phones(workspace_id)
            
            return phone
            
        finally:
            await lk_api.aclose()
    
    @staticmethod
    async def delete_inbound_number(phone_id: str, workspace_id: str = None) -> bool:
        """Delete an inbound phone number and its LiveKit resources."""
        from livekit import api
        from shared.settings import config
        
        db = get_database()
        
        # Get the phone number first
        query = {"phone_id": phone_id}
        if workspace_id:
            query["workspace_id"] = workspace_id
        doc = await db.phone_numbers.find_one(query)
        
        if not doc:
            return False
        
        phone = PhoneNumber.from_dict(doc)
        
        # Delete LiveKit resources if they exist
        if phone.dispatch_rule_id or phone.inbound_trunk_id:
            try:
                lk_api = api.LiveKitAPI(
                    url=config.LIVEKIT_URL,
                    api_key=config.LIVEKIT_API_KEY,
                    api_secret=config.LIVEKIT_API_SECRET,
                )
                
                # Delete dispatch rule first
                if phone.dispatch_rule_id:
                    await lk_api.sip.delete_sip_dispatch_rule(
                        api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=phone.dispatch_rule_id)
                    )
                    logger.info(f"Deleted dispatch rule: {phone.dispatch_rule_id}")
                
                # Then delete trunk
                if phone.inbound_trunk_id:
                    await lk_api.sip.delete_sip_trunk(
                        api.DeleteSIPTrunkRequest(sip_trunk_id=phone.inbound_trunk_id)
                    )
                    logger.info(f"Deleted inbound trunk: {phone.inbound_trunk_id}")
                
                await lk_api.aclose()
            except Exception as e:
                logger.error(f"Error cleaning up LiveKit resources: {e}")
        
        # Delete from database
        result = await db.phone_numbers.delete_one(query)
        if result.deleted_count > 0:
            if workspace_id:
                await SessionCache.invalidate_phones(workspace_id)
            return True
        return False


class SipConfigService:
    """Service for managing SIP configurations."""
    
    @staticmethod
    async def create_sip_config(request: CreateSipConfigRequest) -> SipConfig:
        """Create a new SIP configuration and optionally create LiveKit trunk."""
        from livekit import api
        from shared.settings import config
        
        db = get_database()
        
        # If this is set as default, unset other defaults
        if request.is_default:
            await db.sip_configs.update_many({}, {"$set": {"is_default": False}})
        
        trunk_id = request.trunk_id
        
        # If no trunk_id provided, create a new LiveKit outbound trunk
        if not trunk_id:
            try:
                lk_api = api.LiveKitAPI(
                    url=config.LIVEKIT_URL,
                    api_key=config.LIVEKIT_API_KEY,
                    api_secret=config.LIVEKIT_API_SECRET,
                )
                
                # Create outbound trunk with provided credentials
                trunk_request = api.CreateSIPOutboundTrunkRequest(
                    trunk=api.SIPOutboundTrunkInfo(
                        name=request.name,
                        address=request.sip_domain,
                        numbers=[request.from_number],  # Caller ID numbers
                        auth_username=request.sip_username,
                        auth_password=request.sip_password,
                    )
                )
                
                trunk = await lk_api.sip.create_sip_outbound_trunk(trunk_request)
                trunk_id = trunk.sip_trunk_id
                await lk_api.aclose()
                
                logger.info(f"Created LiveKit trunk: {trunk_id}")
                
            except Exception as e:
                logger.error(f"Failed to create LiveKit trunk: {e}")
                raise
        
        sip = SipConfig(
            name=request.name,
            sip_domain=request.sip_domain,
            sip_username=request.sip_username,
            sip_password=request.sip_password,
            from_number=request.from_number,
            trunk_id=trunk_id,
            description=request.description,
            is_default=request.is_default,
        )
        
        await db.sip_configs.insert_one(sip.to_dict())
        logger.info(f"Created SIP config: {sip.sip_id} - {sip.name} (trunk: {trunk_id})")
        
        # Invalidate SIP cache (global for now, could be workspace-scoped)
        await SessionCache.delete_pattern("ws:*:sip")
        
        return sip
    
    @staticmethod
    async def list_sip_configs(is_active: Optional[bool] = None) -> List[SipConfig]:
        """List all SIP configurations."""
        db = get_database()
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        
        cursor = db.sip_configs.find(query).sort("created_at", -1)
        
        configs = []
        async for doc in cursor:
            configs.append(SipConfig.from_dict(doc))
        
        return configs
    
    @staticmethod
    async def get_sip_config(sip_id: str) -> Optional[SipConfig]:
        """Get a SIP config by ID."""
        db = get_database()
        doc = await db.sip_configs.find_one({"sip_id": sip_id})
        if doc:
            return SipConfig.from_dict(doc)
        return None
    
    @staticmethod
    async def get_default_sip_config() -> Optional[SipConfig]:
        """Get the default SIP configuration."""
        db = get_database()
        doc = await db.sip_configs.find_one({"is_default": True, "is_active": True})
        if doc:
            return SipConfig.from_dict(doc)
        return None
    
    @staticmethod
    async def update_sip_config(sip_id: str, request: UpdateSipConfigRequest) -> Optional[SipConfig]:
        """Update a SIP configuration."""
        db = get_database()
        
        updates = {}
        update_data = request.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            if value is not None:
                updates[key] = value
        
        # If setting as default, unset other defaults
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
                # Invalidate SIP cache
                await SessionCache.delete_pattern("ws:*:sip")
                return SipConfig.from_dict(result)
        
        return None
    
    @staticmethod
    async def delete_sip_config(sip_id: str) -> bool:
        """Delete a SIP configuration."""
        db = get_database()
        result = await db.sip_configs.delete_one({"sip_id": sip_id})
        if result.deleted_count > 0:
            # Invalidate SIP cache
            await SessionCache.delete_pattern("ws:*:sip")
            return True
        return False
