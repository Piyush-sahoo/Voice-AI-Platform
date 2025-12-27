"""Database package for MongoDB operations."""
from .connection import get_database, connect_to_database, close_database_connection
from .models import (
    # Call models
    CallRecord,
    CallStatus,
    CallAnalysis,
    CreateCallRequest,
    CallResponse,
    # Assistant models
    Assistant,
    VoiceConfig,
    ToolDefinition,
    CreateAssistantRequest,
    UpdateAssistantRequest,
    AssistantResponse,
)

__all__ = [
    # Connection
    "get_database",
    "connect_to_database", 
    "close_database_connection",
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
]
