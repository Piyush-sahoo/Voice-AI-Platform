"""
Call record models and schemas.
"""
from datetime import datetime, timezone
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
    sentiment: str = "neutral"
    summary: str = ""
    key_topics: List[str] = []
    action_items: List[str] = []
    analyzed_at: Optional[datetime] = None


class CallRecord(BaseModel):
    """Complete call record stored in MongoDB."""
    call_id: str
    workspace_id: Optional[str] = None  # For multi-tenancy
    phone_number: str  # To number
    from_number: Optional[str] = None  # Caller ID
    status: CallStatus = CallStatus.INITIATED
    duration_seconds: int = 0
    
    # References
    assistant_id: Optional[str] = None
    sip_id: Optional[str] = None  # SIP config used
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CallRecord":
        """Create from MongoDB document."""
        if "_id" in data:
            del data["_id"]
        
        # Handle transcript format variations
        # Handle transcript format variations
        transcript = data.get("transcript")
        # Legacy format: {"messages": [...]}
        if isinstance(transcript, dict):
            if "messages" in transcript:
                data["transcript"] = transcript.get("messages", [])
            elif "items" in transcript: # Handle items too if it exists
                data["transcript"] = transcript.get("items", [])
        elif transcript is None:
             data["transcript"] = []
        
        return cls(**data)


class CreateCallRequest(BaseModel):
    """Request body for creating a new call."""
    phone_number: str
    assistant_id: Optional[str] = None  # Use assistant config
    sip_id: Optional[str] = None  # Use specific SIP config (or default)
    from_number: Optional[str] = None  # Override caller ID
    instructions: Optional[str] = None  # Override assistant instructions
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class CallResponse(CallRecord):
    """Response for call operations."""
    message: Optional[str] = None
    
    @classmethod
    def from_call_record(cls, record: CallRecord, message: str = None) -> "CallResponse":
        """Create response from call record."""
        data = record.model_dump()
        if message:
            data["message"] = message
        return cls(**data)

