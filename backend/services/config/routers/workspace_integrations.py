"""Workspace integrations API endpoints - Config Service."""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from shared.auth.dependencies import get_current_user
from shared.auth.models import User
from services.config.workspace_integrations_service import WorkspaceIntegrationService


logger = logging.getLogger("api.workspace_integrations")
router = APIRouter()


class LiveKitInput(BaseModel):
    url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class AIProvidersInput(BaseModel):
    openai_key: Optional[str] = None
    deepgram_key: Optional[str] = None
    google_key: Optional[str] = None
    elevenlabs_key: Optional[str] = None
    cartesia_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    assemblyai_key: Optional[str] = None


class TelephonyInput(BaseModel):
    sip_domain: Optional[str] = None
    sip_username: Optional[str] = None
    sip_password: Optional[str] = None
    outbound_number: Optional[str] = None


class WorkspaceIntegrationsInput(BaseModel):
    livekit: Optional[LiveKitInput] = None
    ai_providers: Optional[AIProvidersInput] = None
    telephony: Optional[TelephonyInput] = None


def _to_service_payload(body: WorkspaceIntegrationsInput) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if body.livekit is not None:
        data["livekit"] = body.livekit.model_dump(exclude_unset=True)
    if body.ai_providers is not None:
        data["ai_providers"] = body.ai_providers.model_dump(exclude_unset=True)
    if body.telephony is not None:
        data["telephony"] = body.telephony.model_dump(exclude_unset=True)
    return data


def _ensure_workspace_owner(user: User) -> None:
    role = getattr(user, "role", None)
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can manage integrations")


@router.post("/workspace/integrations")
async def create_workspace_integrations(
    body: WorkspaceIntegrationsInput,
    user: User = Depends(get_current_user),
):
    _ensure_workspace_owner(user)
    payload = _to_service_payload(body)
    try:
        doc = await WorkspaceIntegrationService.create_workspace_integrations(user.workspace_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await WorkspaceIntegrationService.get_workspace_integrations(user.workspace_id, redacted=True)


@router.get("/workspace/integrations")
async def get_workspace_integrations(
    user: User = Depends(get_current_user),
):
    result = await WorkspaceIntegrationService.get_workspace_integrations(user.workspace_id, redacted=True)
    if not result:
        raise HTTPException(status_code=404, detail="Workspace integrations not found")
    return result


@router.patch("/workspace/integrations")
async def update_workspace_integrations(
    body: WorkspaceIntegrationsInput,
    user: User = Depends(get_current_user),
):
    _ensure_workspace_owner(user)
    payload = _to_service_payload(body)
    updated = await WorkspaceIntegrationService.update_workspace_integrations(user.workspace_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Workspace integrations not found")
    return await WorkspaceIntegrationService.get_workspace_integrations(user.workspace_id, redacted=True)


@router.delete("/workspace/integrations")
async def delete_workspace_integrations(
    user: User = Depends(get_current_user),
):
    _ensure_workspace_owner(user)
    deleted = await WorkspaceIntegrationService.delete_workspace_integrations(user.workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workspace integrations not found")
    return {"message": "Workspace integrations deleted"}

