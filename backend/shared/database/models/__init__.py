"""Database models package."""
from .call import CallRecord, CallStatus, CallAnalysis, CreateCallRequest, CallResponse
from .assistant import (
    Assistant, 
    VoiceConfig, 
    ToolDefinition,
    CreateAssistantRequest, 
    UpdateAssistantRequest, 
    AssistantResponse,
)
from .phone_sip import (
    PhoneNumber,
    SipConfig,
    CreatePhoneNumberRequest,
    CreateInboundNumberRequest,
    CreateSipConfigRequest,
    UpdateSipConfigRequest,
)
from .campaign import (
    Campaign,
    CampaignStatus,
    CampaignContact,
    CreateCampaignRequest,
    UpdateCampaignRequest,
    CampaignResponse,
)
from .tool import (
    Tool,
    ToolParameter,
    CreateToolRequest,
    UpdateToolRequest,
    ToolResponse,
)

__all__ = [
    # Call models
    "CallRecord",
    "CallStatus", 
    "CallAnalysis",
    "CreateCallRequest",
    "CallResponse",
    # Assistant models
    "Assistant",
    "VoiceConfig",
    "ToolDefinition",
    "CreateAssistantRequest",
    "UpdateAssistantRequest",
    "AssistantResponse",
    # Phone/SIP models
    "PhoneNumber",
    "SipConfig",
    "CreatePhoneNumberRequest",
    "CreateSipConfigRequest",
    "UpdateSipConfigRequest",
    # Campaign models
    "Campaign",
    "CampaignStatus",
    "CampaignContact",
    "CreateCampaignRequest",
    "UpdateCampaignRequest",
    "CampaignResponse",
    # Tool models
    "Tool",
    "ToolParameter",
    "CreateToolRequest",
    "UpdateToolRequest",
    "ToolResponse",
]
