"""
Database models and schemas for call records.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"


class CallAnalysis(BaseModel):
    """Post-call analysis results from Gemini."""
    success: bool = False
    sentiment: str = "neutral"  # positive, neutral, negative
    summary: str = ""
    key_topics: List[str] = []
    action_items: List[str] = []
    analyzed_at: Optional[datetime] = None


class CallRecord(BaseModel):
    """Complete call record stored in MongoDB."""
    call_id: str
    workspace_id: Optional[str] = None  # For multi-tenancy
    phone_number: str
    status: CallStatus = CallStatus.INITIATED
    duration_seconds: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Content
    transcript: List[Dict[str, Any]] = []
    transcript_url: Optional[str] = None
    recording_url: Optional[str] = None
    
    # Custom data
    instructions: Optional[str] = None
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    # Analysis
    analysis: Optional[CallAnalysis] = None
    
    # Tracking
    webhook_sent: bool = False
    egress_id: Optional[str] = None
    room_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = self.model_dump()
        # Convert enums to strings
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CallRecord":
        """Create from MongoDB document."""
        if "_id" in data:
            del data["_id"]  # Remove MongoDB's _id field
        return cls(**data)


class CreateCallRequest(BaseModel):
    """Request body for creating a new call."""
    phone_number: str
    instructions: Optional[str] = None
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class CallResponse(BaseModel):
    """Response for call creation."""
    call_id: str
    status: str
    room_name: str
    message: str = "Call initiated successfully"
