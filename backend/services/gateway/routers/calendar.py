"""Calendar booking proxy endpoints."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4
from urllib.parse import urlencode
import os

import httpx
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from shared.database.connection import get_database
from shared.settings import config

logger = logging.getLogger("api.calendar")
router = APIRouter()


def _frontend_redirect_base() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173")


async def _refresh_google_access_token(refresh_token: str) -> dict:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/calendar/google/callback")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
        response.raise_for_status()
        return response.json()


@router.get("/calendar/google/connect")
async def connect_google_calendar(workspace_id: str = Query(...)):
    """Redirect user to Google OAuth consent screen for calendar connection."""
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/calendar/google/callback")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google OAuth client is not configured")

    query = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar",
        "access_type": "offline",
        "prompt": "consent",
        "state": workspace_id,
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(query)}"
    return RedirectResponse(url=url)


@router.get("/calendar/google/callback")
async def google_calendar_callback(code: str = Query(...), state: str = Query(...)):
    """Handle Google OAuth callback and store workspace calendar credentials."""
    workspace_id = state.strip()
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Missing workspace_id in OAuth state")

    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/calendar/google/callback")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            token_resp = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
            token_resp.raise_for_status()
            token_data = token_resp.json()
    except Exception as e:
        logger.error("Google OAuth token exchange failed: workspace_id=%s error=%s", workspace_id, e)
        raise HTTPException(status_code=502, detail="Google OAuth token exchange failed")

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Missing access_token from Google OAuth")

    db = get_database()
    existing = await db.workspace_calendars.find_one({"workspace_id": workspace_id, "provider": "google"})
    effective_refresh_token = refresh_token or (existing.get("refresh_token") if existing else None)

    doc = {
        "workspace_id": workspace_id,
        "provider": "google",
        "access_token": access_token,
        "refresh_token": effective_refresh_token,
        "calendar_id": "primary",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.workspace_calendars.update_one(
        {"workspace_id": workspace_id, "provider": "google"},
        {"$set": doc},
        upsert=True,
    )

    logger.info("Google calendar connected: workspace_id=%s", workspace_id)
    return RedirectResponse(url=f"{_frontend_redirect_base()}/settings?calendar=connected")


class BookCalendarRequest(BaseModel):
    workspace_id: str
    assistant_id: str
    call_id: str
    name: str
    phone: Optional[str] = None
    date: str
    time: str


@router.post("/calendar/book")
async def book_calendar_event(
    request: BookCalendarRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Book calendar meeting by workspace through backend proxy (no direct Google access from agent)."""
    if x_api_key != config.INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal API key")

    if not request.workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    db = get_database()

    calendar_conn = await db.workspace_calendars.find_one(
        {
            "workspace_id": request.workspace_id,
            "provider": "google",
        }
    )
    if not calendar_conn:
        raise HTTPException(status_code=404, detail="No Google calendar connection for workspace")

    access_token = calendar_conn.get("access_token")
    refresh_token = calendar_conn.get("refresh_token")
    calendar_id = calendar_conn.get("calendar_id") or "primary"
    if not access_token:
        raise HTTPException(status_code=400, detail="Google calendar access token missing")

    try:
        meeting_start = datetime.fromisoformat(f"{request.date}T{request.time}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    meeting_end = meeting_start + timedelta(minutes=30)

    event_payload = {
    "summary": f"Call booking - {request.name}",
    "description": f"Booked by voice agent\nCall ID: {request.call_id}\nPhone: {request.phone or 'N/A'}",
    "start": {
        "dateTime": meeting_start.isoformat(),
        "timeZone": "Asia/Kolkata"
    },
    "end": {
        "dateTime": meeting_end.isoformat(),
        "timeZone": "Asia/Kolkata"
    },
    "conferenceData": {
        "createRequest": {
            "requestId": uuid4().hex,
            "conferenceSolutionKey": {"type": "hangoutsMeet"},
        }
    },
} 

    google_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                google_url,
                params={"conferenceDataVersion": 1},
                json=event_payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 401 and refresh_token:
                refreshed = await _refresh_google_access_token(refresh_token)
                access_token = refreshed.get("access_token")
                if not access_token:
                    raise HTTPException(status_code=502, detail="Token refresh failed")

                await db.workspace_calendars.update_one(
                    {"workspace_id": request.workspace_id, "provider": "google"},
                    {"$set": {"access_token": access_token}},
                )

                response = await client.post(
                    google_url,
                    params={"conferenceDataVersion": 1},
                    json=event_payload,
                    headers={"Authorization": f"Bearer {access_token}"},
                )

            response.raise_for_status()
            event = response.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.text
        logger.error("Calendar booking failed: workspace_id=%s call_id=%s status=%s body=%s", request.workspace_id, request.call_id, e.response.status_code, detail)
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.error("Calendar booking request error: workspace_id=%s call_id=%s error=%s", request.workspace_id, request.call_id, e)
        raise HTTPException(status_code=502, detail="Failed to reach Google Calendar API")

    booking_id = f"book_{uuid4().hex[:12]}"
    meeting_link = event.get("hangoutLink")

    booking_doc = {
        "booking_id": booking_id,
        "workspace_id": request.workspace_id,
        "assistant_id": request.assistant_id,
        "call_id": request.call_id,
        "customer_name": request.name,
        "customer_phone": request.phone,
        "meeting_time": meeting_start.isoformat(),
        "calendar_event_id": event.get("id"),
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.bookings.insert_one(booking_doc)

    logger.info(
        "Calendar booking confirmed: workspace_id=%s assistant_id=%s call_id=%s booking_id=%s event_id=%s",
        request.workspace_id,
        request.assistant_id,
        request.call_id,
        booking_id,
        event.get("id"),
    )

    return {
        "status": "confirmed",
        "booking_id": booking_id,
        "event_id": event.get("id"),
        "meeting_link": meeting_link,
    }
