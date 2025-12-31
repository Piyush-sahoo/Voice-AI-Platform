"""
Phone Number and SIP Configuration models.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class PhoneNumber(BaseModel):
    """Phone number configuration stored in database."""
    phone_id: str = Field(default_factory=lambda: f"ph_{uuid.uuid4().hex[:12]}")
    workspace_id: Optional[str] = None  # For multi-tenancy
    number: str  # E.164 format
    label: Optional[str] = None  # e.g., "Main Sales Line"
    provider: str = "vobiz"
    
    # Call direction: "inbound" | "outbound" | "both"
    direction: str = "outbound"
    
    # Inbound-specific fields
    assistant_id: Optional[str] = None  # Agent that answers inbound calls
    inbound_trunk_id: Optional[str] = None  # LiveKit inbound trunk ID
    dispatch_rule_id: Optional[str] = None  # LiveKit dispatch rule ID
    allowed_addresses: list = Field(default_factory=lambda: ["0.0.0.0/0"])  # IP whitelist
    krisp_enabled: bool = True  # Noise cancellation
    
    # Outbound-specific fields
    sip_config_id: Optional[str] = None  # SIP config for outbound calls
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhoneNumber":
        """Create from MongoDB document."""
        if "_id" in data:
            del data["_id"]
        return cls(**data)


class SipConfig(BaseModel):
    """SIP trunk configuration stored in database."""
    sip_id: str = Field(default_factory=lambda: f"sip_{uuid.uuid4().hex[:12]}")
    workspace_id: Optional[str] = None  # For multi-tenancy
    name: str  # e.g., "Vobiz Production"
    
    # SIP Credentials (for dynamic trunk creation)
    sip_domain: str  # e.g., "867a351f.sip.vobiz.ai"
    sip_username: str
    sip_password: str
    from_number: str  # Caller ID number
    
    # LiveKit trunk ID (created dynamically or provided)
    trunk_id: Optional[str] = None
    
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SipConfig":
        """Create from MongoDB document."""
        if "_id" in data:
            del data["_id"]
        return cls(**data)


# Request/Response models
class CreatePhoneNumberRequest(BaseModel):
    """Request to add a phone number (outbound)."""
    number: str
    label: Optional[str] = None
    provider: str = "vobiz"
    sip_config_id: Optional[str] = None  # SIP config for outbound


class CreateInboundNumberRequest(BaseModel):
    """Request to set up an inbound phone number."""
    number: str  # E.164 format
    label: Optional[str] = None
    assistant_id: str  # Required: which agent answers calls
    allowed_addresses: list = ["0.0.0.0/0"]  # IP whitelist
    krisp_enabled: bool = True  # Noise cancellation
    provider: str = "vobiz"


class CreateSipConfigRequest(BaseModel):
    """Request to create a SIP configuration."""
    name: str
    sip_domain: str  # Required: e.g., "867a351f.sip.vobiz.ai"
    sip_username: str  # Required
    sip_password: str  # Required
    from_number: str  # Required: Caller ID number e.g., "+912271264280"
    trunk_id: Optional[str] = None  # Optional: if not provided, will create one
    description: Optional[str] = None
    is_default: bool = False


class UpdateSipConfigRequest(BaseModel):
    """Request to update a SIP configuration."""
    name: Optional[str] = None
    sip_domain: Optional[str] = None
    sip_username: Optional[str] = None
    sip_password: Optional[str] = None
    trunk_id: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
