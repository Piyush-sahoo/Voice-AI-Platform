"""
Workspace integrations model for per-workspace credentials.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class LiveKitIntegration(BaseModel):
    """LiveKit credentials for a workspace."""

    url: Optional[str] = None
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None


class AIProvidersIntegration(BaseModel):
    """AI provider credentials for a workspace."""

    openai_key_encrypted: Optional[str] = None
    deepgram_key_encrypted: Optional[str] = None
    google_key_encrypted: Optional[str] = None
    elevenlabs_key_encrypted: Optional[str] = None
    cartesia_key_encrypted: Optional[str] = None
    anthropic_key_encrypted: Optional[str] = None
    assemblyai_key_encrypted: Optional[str] = None


class TelephonyIntegration(BaseModel):
    """SIP / telephony credentials for a workspace."""

    sip_domain: Optional[str] = None
    sip_username: Optional[str] = None
    sip_password_encrypted: Optional[str] = None
    outbound_number: Optional[str] = None


class WorkspaceIntegrations(BaseModel):
    """Root document for workspace-specific integrations."""

    workspace_id: str
    livekit: LiveKitIntegration = Field(default_factory=LiveKitIntegration)
    ai_providers: AIProvidersIntegration = Field(default_factory=AIProvidersIntegration)
    telephony: TelephonyIntegration = Field(default_factory=TelephonyIntegration)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceIntegrations":
        if "_id" in data:
            del data["_id"]
        return cls(**data)

