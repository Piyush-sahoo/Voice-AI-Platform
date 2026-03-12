"""Calendar integration and booking routes (workspace-scoped)."""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from shared.settings import config
from shared.auth.dependencies import get_current_user
from shared.auth.models import User
from services.config.workspace_calendar_service import WorkspaceCalendarService

logger = logging.getLogger("calendar_router")

router = APIRouter()


@router.get("/calendar/google/connect-url")
async def google_connect_url(user: User = Depends(get_current_user)):
    """Return the Google OAuth URL for the current workspace (no redirect)."""
    workspace_id = getattr(user, "workspace_id", None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Workspace context is required")

    client_id = config.GOOGLE_OAUTH_CLIENT_ID
    client_secret = config.GOOGLE_OAUTH_CLIENT_SECRET
    redirect_uri = config.GOOGLE_REDIRECT_URI or config.GOOGLE_OAUTH_REDIRECT_URI

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=501,
            detail="Google Calendar integration not configured",
        )

    base = "https://accounts.google.com/o/oauth2/v2/auth"
    scope = "https://www.googleapis.com/auth/calendar"
    params = (
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={workspace_id}"
    )
    auth_url = f"{base}?{params}"
    return {"url": auth_url}


@router.get("/calendar/google/connect", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def google_connect(user: User = Depends(get_current_user)):
    """Start Google OAuth flow for the current workspace."""
    workspace_id = getattr(user, "workspace_id", None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Workspace context is required")

    client_id = config.GOOGLE_OAUTH_CLIENT_ID
    client_secret = config.GOOGLE_OAUTH_CLIENT_SECRET
    redirect_uri = config.GOOGLE_REDIRECT_URI or config.GOOGLE_OAUTH_REDIRECT_URI

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=501,
            detail="Google Calendar integration not configured",
        )

    base = "https://accounts.google.com/o/oauth2/v2/auth"
    scope = "https://www.googleapis.com/auth/calendar"
    params = (
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={workspace_id}"
    )
    auth_url = f"{base}?{params}"
    logger.info("Redirecting workspace %s to Google OAuth consent screen", workspace_id)
    return RedirectResponse(auth_url)


@router.get("/calendar/google/auth", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def google_auth(user: User = Depends(get_current_user)):
    """Alias route for starting Google OAuth flow."""
    return await google_connect(user)


@router.get("/calendar/google/callback")
async def google_callback(code: Optional[str] = None, state: Optional[str] = None):
    """Handle Google OAuth callback and persist workspace calendar credentials."""
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    workspace_id = state
    client_id = config.GOOGLE_OAUTH_CLIENT_ID
    client_secret = config.GOOGLE_OAUTH_CLIENT_SECRET
    redirect_uri = config.GOOGLE_REDIRECT_URI or config.GOOGLE_OAUTH_REDIRECT_URI

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(token_url, data=data)
    if resp.status_code != 200:
        logger.error("Google token exchange failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Failed to exchange code with Google")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        logger.error("Google token response missing access_token: %s", token_data)
        raise HTTPException(status_code=502, detail="Invalid token response from Google")

    await WorkspaceCalendarService.upsert_google_calendar(
        workspace_id=workspace_id,
        access_token=access_token,
        refresh_token=refresh_token,
        calendar_id="primary",
    )
    logger.info("Google Calendar connected for workspace %s", workspace_id)

    frontend_url = config.FRONTEND_URL or "http://localhost:3000"
    return RedirectResponse(f"{frontend_url}/settings?calendar=connected")


class BookCalendarRequest(BaseModel):
    workspace_id: str
    assistant_id: str
    call_id: str
    name: str
    phone: Optional[str] = None
    date: str  # YYYY-MM-DD
    time: str  # HH:MM


@router.post("/calendar/book")
async def book_calendar_event(
    request: BookCalendarRequest,
    x_api_key: str = Header(default="", alias="X-API-Key"),
):
    """Internal-only endpoint to book a calendar event for a workspace."""
    if x_api_key != config.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized internal request")

    if not request.workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    # Build naive start/end datetimes; timezone handling can be refined later.
    from datetime import datetime, timedelta

    try:
        meeting_start = datetime.fromisoformat(f"{request.date}T{request.time}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date or time format")

    meeting_end = meeting_start + timedelta(minutes=30)

    cal = await WorkspaceCalendarService.get_google_calendar(request.workspace_id, decrypt=True)
    if not cal:
        raise HTTPException(status_code=404, detail="No Google calendar connected for this workspace")

    access_token = cal.get("access_token")
    refresh_token = cal.get("refresh_token")
    calendar_id = cal.get("calendar_id") or "primary"

    event_payload = {
        "summary": f"Call booking with {request.name}",
        "description": f"Call ID: {request.call_id}\nAssistant: {request.assistant_id}\nPhone: {request.phone or 'N/A'}",
        "start": {
            "dateTime": meeting_start.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": meeting_end.isoformat(),
            "timeZone": "UTC",
        },
        "conferenceData": {
            "createRequest": {
                "requestId": f"{request.call_id}-{int(meeting_start.timestamp())}"
            }
        },
    }

    async def _create_event(token: str):
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?conferenceDataVersion=1"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=event_payload, headers=headers)
        return resp

    resp = await _create_event(access_token)
    if resp.status_code == 401 and refresh_token:
        # Try to refresh access token once
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": config.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": config.GOOGLE_OAUTH_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(token_url, data=data)
        if token_resp.status_code == 200:
            new_access = token_resp.json().get("access_token")
            if new_access:
                await WorkspaceCalendarService.update_google_access_token(request.workspace_id, new_access)
                resp = await _create_event(new_access)

    if resp.status_code >= 400:
        logger.error("Google Calendar event creation failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Failed to create calendar event")

    event = resp.json()
    meeting_link = None
    try:
        conference = event.get("conferenceData", {})
        entry_points = conference.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                meeting_link = ep.get("uri")
                break
    except Exception:
        meeting_link = None

    return {
        "status": "confirmed",
        "event_id": event.get("id"),
        "meeting_start": meeting_start.isoformat(),
        "meeting_end": meeting_end.isoformat(),
        "meeting_link": meeting_link,
        "message": "Your meeting has been booked.",
    }

