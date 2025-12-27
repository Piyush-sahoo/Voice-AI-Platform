"""
Tool service for managing custom function calling tools.
"""
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from database.models import (
    Tool,
    ToolParameter,
    CreateToolRequest,
    UpdateToolRequest,
)
from database.connection import get_database

logger = logging.getLogger("tool_service")


class ToolService:
    """Service for managing custom tools."""
    
    @staticmethod
    async def create_tool(request: CreateToolRequest) -> Tool:
        """Create a new tool."""
        db = get_database()
        
        # Convert parameter dicts to ToolParameter objects
        parameters = []
        for p in request.parameters:
            parameters.append(ToolParameter(
                name=p.get("name"),
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", True),
                enum=p.get("enum"),
                default=p.get("default"),
            ))
        
        tool = Tool(
            name=request.name,
            description=request.description,
            type=request.type,
            webhook_url=request.webhook_url,
            http_method=request.http_method,
            headers=request.headers,
            parameters=parameters,
            speak_response=request.speak_response,
            response_template=request.response_template,
        )
        
        await db.tools.insert_one(tool.to_dict())
        logger.info(f"Created tool: {tool.tool_id} - {tool.name}")
        
        return tool
    
    @staticmethod
    async def get_tool(tool_id: str) -> Optional[Tool]:
        """Get a tool by ID."""
        db = get_database()
        doc = await db.tools.find_one({"tool_id": tool_id})
        if doc:
            return Tool.from_dict(doc)
        return None
    
    @staticmethod
    async def get_tool_by_name(name: str) -> Optional[Tool]:
        """Get a tool by name."""
        db = get_database()
        doc = await db.tools.find_one({"name": name, "is_active": True})
        if doc:
            return Tool.from_dict(doc)
        return None
    
    @staticmethod
    async def list_tools(is_active: Optional[bool] = None) -> List[Tool]:
        """List all tools."""
        db = get_database()
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        
        cursor = db.tools.find(query).sort("created_at", -1)
        
        tools = []
        async for doc in cursor:
            tools.append(Tool.from_dict(doc))
        
        return tools
    
    @staticmethod
    async def update_tool(tool_id: str, request: UpdateToolRequest) -> Optional[Tool]:
        """Update a tool."""
        db = get_database()
        
        updates = {}
        update_data = request.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            if value is not None:
                updates[key] = value
        
        if updates:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await db.tools.find_one_and_update(
                {"tool_id": tool_id},
                {"$set": updates},
                return_document=True,
            )
            
            if result:
                return Tool.from_dict(result)
        
        return None
    
    @staticmethod
    async def delete_tool(tool_id: str) -> bool:
        """Delete a tool."""
        db = get_database()
        result = await db.tools.delete_one({"tool_id": tool_id})
        return result.deleted_count > 0
    
    @staticmethod
    async def execute_tool(tool: Tool, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the response."""
        if tool.type == "webhook" and tool.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if tool.http_method.upper() == "GET":
                        response = await client.get(
                            tool.webhook_url,
                            params=arguments,
                            headers=tool.headers,
                        )
                    else:
                        response = await client.post(
                            tool.webhook_url,
                            json=arguments,
                            headers=tool.headers,
                        )
                    
                    if response.status_code >= 200 and response.status_code < 300:
                        result = response.text
                        
                        # Apply response template if provided
                        if tool.response_template:
                            try:
                                data = response.json()
                                result = tool.response_template.format(**data)
                            except Exception:
                                pass
                        
                        logger.info(f"Tool {tool.name} executed successfully")
                        return result
                    else:
                        logger.error(f"Tool {tool.name} failed: {response.status_code}")
                        return f"Sorry, the {tool.name} service is unavailable."
                        
            except Exception as e:
                logger.error(f"Tool {tool.name} error: {e}")
                return f"Sorry, I couldn't complete that action."
        
        return "This tool is not configured for execution."
    
    @staticmethod
    async def get_tools_for_assistant(assistant_id: str) -> List[Dict[str, Any]]:
        """Get tools assigned to an assistant in OpenAI format."""
        # For now, return all active tools
        # Later: can be filtered by assistant's tool list
        tools = await ToolService.list_tools(is_active=True)
        return [tool.to_openai_tool() for tool in tools]
