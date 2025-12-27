"""Tools API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from database.models import CreateToolRequest, UpdateToolRequest, ToolResponse
from services import ToolService
from auth.dependencies import get_current_user
from auth.models import User

logger = logging.getLogger("api.tools")
router = APIRouter()


@router.post("/tools", response_model=ToolResponse)
async def create_tool(request: CreateToolRequest):
    """
    Create a custom function calling tool.
    
    - **name**: Tool function name (no spaces)
    - **description**: What the tool does
    - **webhook_url**: URL to call when tool is invoked
    - **parameters**: List of parameters with name, type, description
    """
    try:
        tool = await ToolService.create_tool(request)
        
        return ToolResponse(
            tool_id=tool.tool_id,
            name=tool.name,
            message="Tool created successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools(is_active: Optional[bool] = Query(None)):
    """List all tools."""
    tools = await ToolService.list_tools(is_active=is_active)
    
    return {
        "tools": [
            {
                "tool_id": t.tool_id,
                "name": t.name,
                "description": t.description,
                "type": t.type,
                "is_active": t.is_active,
            }
            for t in tools
        ],
        "count": len(tools),
    }


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get a tool by ID."""
    tool = await ToolService.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool.to_dict()


@router.patch("/tools/{tool_id}")
async def update_tool(tool_id: str, request: UpdateToolRequest):
    """Update a tool."""
    tool = await ToolService.update_tool(tool_id, request)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return ToolResponse(
        tool_id=tool.tool_id,
        name=tool.name,
        message="Tool updated successfully",
    )


@router.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool."""
    deleted = await ToolService.delete_tool(tool_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"message": "Tool deleted successfully"}


@router.post("/tools/{tool_id}/test")
async def test_tool(tool_id: str, arguments: dict = {}):
    """Test a tool with sample arguments."""
    tool = await ToolService.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    result = await ToolService.execute_tool(tool, arguments)
    
    return {
        "tool_id": tool_id,
        "result": result,
    }
