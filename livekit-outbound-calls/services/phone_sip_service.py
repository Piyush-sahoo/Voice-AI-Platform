"""
Phone Number and SIP Config service.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List

from database.models import (
    PhoneNumber,
    SipConfig,
    CreatePhoneNumberRequest,
    CreateSipConfigRequest,
    UpdateSipConfigRequest,
)
from database.connection import get_database

logger = logging.getLogger("phone_sip_service")


class PhoneNumberService:
    """Service for managing phone numbers."""
    
    @staticmethod
    async def add_phone_number(request: CreatePhoneNumberRequest) -> PhoneNumber:
        """Add a new phone number."""
        db = get_database()
        
        phone = PhoneNumber(
            number=request.number,
            label=request.label,
            provider=request.provider,
        )
        
        await db.phone_numbers.insert_one(phone.to_dict())
        logger.info(f"Added phone number: {phone.phone_id} - {phone.number}")
        
        return phone
    
    @staticmethod
    async def list_phone_numbers(is_active: Optional[bool] = None) -> List[PhoneNumber]:
        """List all phone numbers."""
        db = get_database()
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        
        cursor = db.phone_numbers.find(query).sort("created_at", -1)
        
        phones = []
        async for doc in cursor:
            phones.append(PhoneNumber.from_dict(doc))
        
        return phones
    
    @staticmethod
    async def get_phone_number(phone_id: str) -> Optional[PhoneNumber]:
        """Get a phone number by ID."""
        db = get_database()
        doc = await db.phone_numbers.find_one({"phone_id": phone_id})
        if doc:
            return PhoneNumber.from_dict(doc)
        return None
    
    @staticmethod
    async def delete_phone_number(phone_id: str) -> bool:
        """Delete a phone number."""
        db = get_database()
        result = await db.phone_numbers.delete_one({"phone_id": phone_id})
        return result.deleted_count > 0


class SipConfigService:
    """Service for managing SIP configurations."""
    
    @staticmethod
    async def create_sip_config(request: CreateSipConfigRequest) -> SipConfig:
        """Create a new SIP configuration and optionally create LiveKit trunk."""
        from livekit import api
        from config import config
        
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
                return SipConfig.from_dict(result)
        
        return None
    
    @staticmethod
    async def delete_sip_config(sip_id: str) -> bool:
        """Delete a SIP configuration."""
        db = get_database()
        result = await db.sip_configs.delete_one({"sip_id": sip_id})
        return result.deleted_count > 0
