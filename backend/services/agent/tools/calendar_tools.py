"""Calendar-related tools for voice agent."""
import logging
import os
from typing import Any, Dict
from datetime import datetime

import httpx

logger = logging.getLogger("agent.tools.calendar")

BOOK_MEETING_SCHEMA: Dict[str, Any] = {
    "name": "book_meeting",
    "description": "Book a meeting in the workspace calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "date": {
                "type": "string",
                "description": "Required format: YYYY-MM-DD (example: 2026-03-14)",
            },
            "time": {
                "type": "string",
                "description": "Required format: HH:MM in 24-hour format (example: 15:33)",
            },
        },
        "required": ["name", "date", "time"],
    },
}


def _is_strict_datetime(date: str, time: str) -> bool:
    """Validate strict gateway datetime contract: YYYY-MM-DD and HH:MM (24-hour)."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
        datetime.strptime(time, "%H:%M")
        return True
    except ValueError:
        return False


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
        }

    logger.info(
        "Calendar tool request: workspace_id=%s assistant_id=%s call_id=%s payload=%s",
        workspace_id,
        assistant_id,
        call_id,
        {"name": name, "phone": phone, "date": date, "time": time},
    )

    gateway_url = os.getenv("GATEWAY_INTERNAL_URL", "http://gateway:8000")
    internal_api_key = os.getenv("INTERNAL_API_KEY", "vobiz_internal_secret_key_123")

    if not _is_strict_datetime(date, time):
        logger.warning(
            "Calendar tool rejected non-strict datetime: workspace_id=%s assistant_id=%s call_id=%s date=%s time=%s",
            workspace_id,
            assistant_id,
            call_id,
            date,
            time,
        )
        return {
            "status": "error",
            "error": "Invalid date/time format. Use date as YYYY-MM-DD and time as HH:MM (24-hour).",
            "expected_date_format": "YYYY-MM-DD",
            "expected_time_format": "HH:MM",
            "received_date": date,
            "received_time": time,
        }

    payload = {
        "workspace_id": workspace_id,
        "assistant_id": assistant_id,
        "call_id": call_id,
        "name": name,
        "phone": phone,
        "date": date,
        "time": time,
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Canonical route in this branch is mounted at /api/calendar/book.
            response = await client.post(
                f"{gateway_url}/api/calendar/book",
                json=payload,
                headers={"X-API-Key": internal_api_key},
            )

            # Backward-compat fallback for branches where calendar router has no /api prefix.
            if response.status_code == 404:
                response = await client.post(
                    f"{gateway_url}/calendar/book",
                    json=payload,
                    headers={"X-API-Key": internal_api_key},
                )

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
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