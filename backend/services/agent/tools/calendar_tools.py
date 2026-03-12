import os
from typing import Dict, Any
import logging
from datetime import datetime
import re

import httpx

from shared.settings import config

logger = logging.getLogger("agent.calendar_tools")

# Word-to-number mapping for spelled-out numbers
WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
}


def _convert_words_to_numbers(text: str) -> str:
    """Convert spelled-out numbers in text to digits.
    
    Examples:
    - "March thirteen twenty twenty six" → "March 13 20 26" or similar
    - "Five fifty five PM" → "5 55 PM"
    """
    if not text:
        return text
    
    text_lower = text.lower()
    words = text_lower.split()
    result = []
    
    for word in words:
        # Check if word is a digit word
        if word in WORD_TO_NUM:
            result.append(str(WORD_TO_NUM[word]))
        else:
            result.append(word)
    
    return " ".join(result)


def _parse_spelled_date(text: str) -> str:
    """Parse spelled-out date like 'March thirteen twenty twenty six' to '2026-03-13'.
    
    Handles patterns like:
    - "March thirteen twenty twenty six" → "2026-03-13"
    - "March 13 2026" → "2026-03-13"
    """
    text = text.strip()
    
    # Convert word numbers to digits
    converted = _convert_words_to_numbers(text)
    
    # Try parsing with converted text
    date_formats = [
        "%B %d %Y",  # "March 13 2026"
        "%b %d %Y",  # "Mar 13 2026"
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(converted, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: '{text}'")


def _parse_spelled_time(text: str) -> str:
    """Parse spelled-out time like 'Five fifty five PM' to '17:55'.
    
    Handles patterns like:
    - "Five fifty five PM" → "17:55"
    - "5:55 PM" → "17:55"
    """
    text = text.strip()
    
    # Convert word numbers to digits
    converted = _convert_words_to_numbers(text)
    
    # Try parsing with converted text
    time_formats = [
        "%I %M %p",  # "5 55 PM"
        "%I %p",     # "5 PM"
        "%I:%M %p",  # "5:55 PM"
        "%H:%M",     # "17:55"
        "%H",        # "17"
    ]
    
    for fmt in time_formats:
        try:
            parsed = datetime.strptime(converted, fmt)
            return parsed.strftime("%H:%M")
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse time: '{text}'")


def _normalize_date_time(date: str, time: str) -> tuple[str, str]:
    """Normalize date/time strings to ISO date (YYYY-MM-DD) and time (HH:MM).
    
    Supports both numeric and spelled-out formats:
    - Date: "March 13 2026", "March thirteen twenty twenty six", "2026-03-13"
    - Time: "5:55 PM", "Five fifty five PM", "17:55"
    """
    raw_date = (date or "").strip()
    raw_time = (time or "").strip()

    # Try the new spelled-out date/time parsers first
    try:
        normalized_date = _parse_spelled_date(raw_date)
        normalized_time = _parse_spelled_time(raw_time)
        return normalized_date, normalized_time
    except ValueError:
        pass

    # Fallback to original logic for backwards compatibility
    # First try parsing as a combined datetime.
    combined_candidates = [
        f"{raw_date} {raw_time}",
        f"{raw_date}T{raw_time}",
    ]
    combined_formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%B %d %Y %I:%M %p",
        "%B %d, %Y %I:%M %p",
        "%b %d %Y %I:%M %p",
        "%b %d, %Y %I:%M %p",
    ]
    for value in combined_candidates:
        for fmt in combined_formats:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.strftime("%Y-%m-%d"), parsed.strftime("%H:%M")
            except ValueError:
                continue

    # Parse date independently.
    date_formats = [
        "%Y-%m-%d",
        "%B %d %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(raw_date, fmt)
            break
        except ValueError:
            continue

    # Parse time independently.
    time_formats = [
        "%H:%M",
        "%I:%M %p",
        "%I %p",
    ]
    parsed_time = None
    for fmt in time_formats:
        try:
            parsed_time = datetime.strptime(raw_time, fmt)
            break
        except ValueError:
            continue

    if parsed_date and parsed_time:
        return parsed_date.strftime("%Y-%m-%d"), parsed_time.strftime("%H:%M")

    raise ValueError(f"Unable to normalize date/time: date='{date}' time='{time}'")


async def book_meeting(
    workspace_id: str,
    assistant_id: str,
    call_id: str,
    name: str,
    date: str,
    time: str,
    phone: str = "",
) -> Dict[str, Any]:
    """Call the Gateway to book a calendar meeting for this workspace."""
    internal_key = os.getenv("INTERNAL_API_KEY", config.INTERNAL_API_KEY)
    base_url = os.getenv("GATEWAY_INTERNAL_URL", "http://gateway:8000")
    normalized_date, normalized_time = _normalize_date_time(date, time)
    logger.info(f"Normalized date/time → {normalized_date} {normalized_time}")

    payload = {
        "workspace_id": workspace_id,
        "assistant_id": assistant_id,
        "call_id": call_id,
        "name": name,
        "phone": phone or None,
        "date": normalized_date,
        "time": normalized_time,
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Canonical route is mounted under /api.
        resp = await client.post(
            f"{base_url}/api/calendar/book",
            json=payload,
            headers={"X-API-Key": internal_key},
        )
        # Backward compatibility fallback for older route wiring.
        if resp.status_code == 404:
            resp = await client.post(
                f"{base_url}/calendar/book",
                json=payload,
                headers={"X-API-Key": internal_key},
            )

        resp.raise_for_status()
        return resp.json()


async def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an agent tool by name."""
    logger.info("Executing tool '%s' with args=%s", tool_name, args)

    if tool_name != "book_meeting":
        raise ValueError(f"Unsupported tool: {tool_name}")

    result = await book_meeting(
        workspace_id=args["workspace_id"],
        assistant_id=args["assistant_id"],
        call_id=args["call_id"],
        name=args["name"],
        date=args["date"],
        time=args["time"],
        phone=args.get("phone", ""),
    )
    logger.info(
        "Calendar booking successful: call_id=%s event_id=%s",
        args.get("call_id"),
        result.get("event_id"),
    )
    return result

