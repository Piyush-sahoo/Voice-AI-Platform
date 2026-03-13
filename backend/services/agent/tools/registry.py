"""Tool registry and execution wrapper for agent tools."""
import logging
import time
from typing import Any, Dict

from services.agent.tools.calendar_tools import book_meeting

logger = logging.getLogger("agent.tools.registry")

TOOL_MAP = {
    "book_meeting": book_meeting,
}

async def execute_tool(name: str, args: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tool by name with structured logging."""
    tool = TOOL_MAP.get(name)
    if not tool:
        return {"status": "error", "error": f"tool {name} not found"}

    workspace_id = ctx.get("workspace_id")
    assistant_id = ctx.get("assistant_id")
    call_id = ctx.get("call_id")

    start = time.perf_counter()
    success = False
    try:
        result = await tool(args, ctx)
        success = str(result.get("status", "")).lower() not in {"error", "failed"}
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "TOOL CALL: workspace_id=%s assistant_id=%s call_id=%s tool_name=%s tool_args=%s execution_time_ms=%s success=%s",
            workspace_id,
            assistant_id,
            call_id,
            name,
            args,
            elapsed_ms,
            success,
        )
