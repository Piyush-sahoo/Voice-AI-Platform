"""Calendar-related tools for voice agent."""
import logging
import os
from typing import Any, Dict

import httpx
from dateutil import parser

logger = logging.getLogger("agent.tools.calendar")

BOOK_MEETING_SCHEMA: Dict[str, Any] = {
    "name": "book_meeting",
    "description": "Book a meeting in the workspace calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "date": {"type": "string"},
            "time": {"type": "string"},
        },
        "required": ["name", "date", "time"],
    },
}


async def book_meeting(args: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Book a meeting by calling backend gateway proxy endpoint."""
    name = str(args.get("name") or "").strip()
    phone = str(args.get("phone") or "").strip()
    date = str(args.get("date") or "").strip()
    time = str(args.get("time") or "").strip()

    workspace_id = str(ctx.get("workspace_id") or "").strip()
    assistant_id = str(ctx.get("assistant_id") or "").strip()
    call_id = str(ctx.get("call_id") or "").strip()

    if not workspace_id or not assistant_id or not call_id:
        return {
            "status": "error",
            "error": "missing required context",
            "workspace_id": workspace_id,
            "assistant_id": assistant_id,
            "call_id": call_id,
        }

    gateway_url = os.getenv("GATEWAY_INTERNAL_URL", "http://gateway:8000")
    internal_api_key = os.getenv("INTERNAL_API_KEY", "vobiz_internal_secret_key_123")

    # Normalize natural-language date/time from LLM into gateway ISO formats.
    original_date = date
    original_time = time
    try:
        dt = parser.parse(f"{date} {time}")
        normalized_date = dt.strftime("%Y-%m-%d")
        normalized_time = dt.strftime("%H:%M")
    except Exception as e:
        normalized_date = date
        normalized_time = time
        logger.warning(
            "Calendar tool date/time normalization failed: workspace_id=%s assistant_id=%s call_id=%s original_date=%s original_time=%s error=%s",
            workspace_id,
            assistant_id,
            call_id,
            original_date,
            original_time,
            e,
        )

    logger.info(
        "Calendar tool normalized datetime: workspace_id=%s assistant_id=%s call_id=%s original_date=%s original_time=%s normalized_date=%s normalized_time=%s",
        workspace_id,
        assistant_id,
        call_id,
        original_date,
        original_time,
        normalized_date,
        normalized_time,
    )

    payload = {
        "workspace_id": workspace_id,
        "assistant_id": assistant_id,
        "call_id": call_id,
        "name": name,
        "phone": phone,
        "date": normalized_date,
        "time": normalized_time,
    }

    logger.info(
        "Calendar tool request: workspace_id=%s assistant_id=%s call_id=%s payload=%s",
        workspace_id,
        assistant_id,
        call_id,
        {"name": name, "phone": phone, "date": date, "time": time},
    )

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            response = await client.post(
                f"{gateway_url}/calendar/book",
                json=payload,
                headers={"X-API-Key": internal_api_key},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        body = None
        try:
            body = e.response.json()
        except Exception:
            body = {"detail": e.response.text}
        return {
            "status": "error",
            "error": f"calendar booking failed with status {e.response.status_code}",
            "detail": body,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"calendar booking request failed: {e}",
        }
