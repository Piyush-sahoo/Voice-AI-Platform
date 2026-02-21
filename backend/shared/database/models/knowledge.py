"""Knowledge (RAG) models for document metadata and embedded chunks."""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class KnowledgeSourceType(str, Enum):
    FILE = "file"
    URL = "url"
    TEXT = "text"


class KnowledgeStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class KnowledgeDocument(BaseModel):
    """Metadata for a knowledge source document."""

    id: Optional[str] = None
    workspace_id: Optional[str] = None
    name: str
    source_type: KnowledgeSourceType
    storage_url: Optional[str] = None
    file_size: int = 0
    content_hash: str
    assigned_assistant_ids: List[str] = []
    status: KnowledgeStatus = KnowledgeStatus.PROCESSING
    error_message: Optional[str] = None
    token_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_synced_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["source_type"] = self.source_type.value
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeDocument":
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return cls(**data)


class KnowledgeChunk(BaseModel):
    """Embedded chunk tied to one knowledge document."""

    id: Optional[str] = None
    workspace_id: str
    document_id: str
    document_name: str
    assistant_ids: List[str] = []
    chunk_text: str
    embedding: List[float]
    token_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data.pop("id", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeChunk":
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return cls(**data)
