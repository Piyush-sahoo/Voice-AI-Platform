"""Workspace integrations API endpoints - Gateway proxy to Config Service."""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Request

from shared.auth.dependencies import get_current_user
from shared.auth.models import User
from services.gateway.proxy import proxy_to_config, build_proxy_headers


logger = logging.getLogger("api.workspace_integrations")
router = APIRouter()


@router.post("/workspace/integrations")
async def create_workspace_integrations(
    req: Request,
    user: User = Depends(get_current_user),
):
    headers = build_proxy_headers(req, user.workspace_id)
    body = await req.json()
    result = await proxy_to_config(
        path="/workspace/integrations",
        method="POST",
        headers=headers,
        json_body=body,
    )
    return result


@router.get("/workspace/integrations")
async def get_workspace_integrations(
    req: Request,
    user: User = Depends(get_current_user),
):
    headers = build_proxy_headers(req, user.workspace_id)
    result = await proxy_to_config(
        path="/workspace/integrations",
        method="GET",
        headers=headers,
    )
    return result


@router.patch("/workspace/integrations")
async def update_workspace_integrations(
    req: Request,
    user: User = Depends(get_current_user),
):
    headers = build_proxy_headers(req, user.workspace_id)
    body = await req.json()
    result = await proxy_to_config(
        path="/workspace/integrations",
        method="PATCH",
        headers=headers,
        json_body=body,
    )
    return result


@router.delete("/workspace/integrations")
async def delete_workspace_integrations(
    req: Request,
    user: User = Depends(get_current_user),
):
    headers = build_proxy_headers(req, user.workspace_id)
    result = await proxy_to_config(
        path="/workspace/integrations",
        method="DELETE",
        headers=headers,
    )
    return result

