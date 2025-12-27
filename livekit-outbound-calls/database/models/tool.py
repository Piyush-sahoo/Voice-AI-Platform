"""
Custom Tool models for function calling.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class ToolParameter(BaseModel):
    """Parameter definition for a tool."""
    name: str
    type: str = "string"  # string, number, boolean, array, object
    description: str
    required: bool = True
    enum: Optional[List[str]] = None  # For fixed options
    default: Optional[Any] = None


class Tool(BaseModel):
    """Custom function calling tool stored in database."""
    tool_id: str = Field(default_factory=lambda: f"tool_{uuid.uuid4().hex[:12]}")
    workspace_id: Optional[str] = None  # For multi-tenancy
    name: str  # Function name (no spaces)
    description: str  # What the tool does
    
    # Execution
    type: str = "webhook"  # webhook, http, built-in
    webhook_url: Optional[str] = None  # URL to call
    http_method: str = "POST"
    headers: Dict[str, str] = {}
    
    # Parameters
    parameters: List[ToolParameter] = []
    
    # Response handling
    speak_response: bool = True  # Have agent speak the response
    response_template: Optional[str] = None  # Template for response
    
    # Metadata
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
    def from_dict(cls, data: Dict[str, Any]) -> "Tool":
        """Create from MongoDB document."""
        if "_id" in data:
            del data["_id"]
        return cls(**data)
    
    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


# Request/Response models
class CreateToolRequest(BaseModel):
    """Request to create a custom tool."""
    name: str
    description: str
    type: str = "webhook"
    webhook_url: Optional[str] = None
    http_method: str = "POST"
    headers: Dict[str, str] = {}
    parameters: List[Dict[str, Any]] = []
    speak_response: bool = True
    response_template: Optional[str] = None


class UpdateToolRequest(BaseModel):
    """Request to update a tool."""
    name: Optional[str] = None
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    http_method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    speak_response: Optional[bool] = None
    response_template: Optional[str] = None
    is_active: Optional[bool] = None


class ToolResponse(BaseModel):
    """Response for tool operations."""
    tool_id: str
    name: str
    message: str
