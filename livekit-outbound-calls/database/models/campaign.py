"""
Campaign models for batch calling.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignContact(BaseModel):
    """A contact in a campaign."""
    phone_number: str
    name: Optional[str] = None
    variables: Dict[str, str] = {}  # For personalization
    status: str = "pending"  # pending, called, completed, failed, skipped
    call_id: Optional[str] = None
    called_at: Optional[datetime] = None
    result: Optional[str] = None  # answered, no_answer, busy, failed


class Campaign(BaseModel):
    """Campaign for batch outbound calling."""
    campaign_id: str = Field(default_factory=lambda: f"camp_{uuid.uuid4().hex[:12]}")
    workspace_id: Optional[str] = None  # For multi-tenancy
    name: str
    description: Optional[str] = None
    
    # Configuration
    assistant_id: str  # Required: which assistant to use
    sip_id: Optional[str] = None  # SIP config (or default)
    
    # Contacts
    contacts: List[CampaignContact] = []
    total_contacts: int = 0
    
    # Progress
    status: CampaignStatus = CampaignStatus.DRAFT
    calls_completed: int = 0
    calls_answered: int = 0
    calls_failed: int = 0
    
    # Settings
    max_concurrent_calls: int = 1  # How many calls at once
    retry_failed: bool = False
    max_retries: int = 2
    
    # Schedule
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = self.model_dump()
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.scheduled_at:
            data["scheduled_at"] = self.scheduled_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        """Create from MongoDB document."""
        if "_id" in data:
            del data["_id"]
        return cls(**data)


# Request/Response models
class CreateCampaignRequest(BaseModel):
    """Request to create a campaign."""
    name: str
    description: Optional[str] = None
    assistant_id: str
    sip_id: Optional[str] = None
    contacts: List[Dict[str, Any]]  # List of {phone_number, name?, variables?}
    max_concurrent_calls: int = 1
    retry_failed: bool = False


class UpdateCampaignRequest(BaseModel):
    """Request to update a campaign."""
    name: Optional[str] = None
    description: Optional[str] = None
    max_concurrent_calls: Optional[int] = None
    retry_failed: Optional[bool] = None


class CampaignResponse(BaseModel):
    """Response for campaign operations."""
    campaign_id: str
    name: str
    status: str
    total_contacts: int
    message: str
