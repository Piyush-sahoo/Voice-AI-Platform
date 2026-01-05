"""SIP Configurations API endpoints - Gateway proxy to Config Service."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import CreateSipConfigRequest, UpdateSipConfigRequest
from shared.auth.dependencies import get_current_user
from shared.auth.models import User
from services.gateway.proxy import proxy_to_config, build_proxy_headers

logger = logging.getLogger("api.sip_configs")
router = APIRouter()


@router.post("/sip-configs")
async def create_sip_config(
    request: CreateSipConfigRequest,
    req: Request,
    user: User = Depends(get_current_user)
):
    """Create a new SIP configuration - proxied to Config Service."""
    try:
        headers = build_proxy_headers(req, user.workspace_id)
        result = await proxy_to_config(
            path="/sip-configs",
            method="POST",
            headers=headers,
            json_body=request.model_dump(),
        )
        logger.info(f"Created SIP config via Config Service: {result.get('sip_id')} (workspace: {user.workspace_id})")
        return result
    except Exception as e:
        logger.error(f"Failed to create SIP config: {e}")
        raise


@router.get("/sip-configs")
async def list_sip_configs(
    is_active: Optional[bool] = Query(None),
    req: Request = None,
    user: User = Depends(get_current_user)
):
    """List SIP configurations - proxied to Config Service."""
    headers = build_proxy_headers(req, user.workspace_id)
    query_params = {}
    if is_active is not None:
        query_params["is_active"] = is_active
    
    result = await proxy_to_config(
        path="/sip-configs",
        method="GET",
        headers=headers,
        query_params=query_params,
    )
    return result


@router.get("/sip-configs/{sip_id}")
async def get_sip_config(
    sip_id: str,
    req: Request,
    user: User = Depends(get_current_user)
):
    """Get a specific SIP configuration - proxied to Config Service."""
    headers = build_proxy_headers(req, user.workspace_id)
    result = await proxy_to_config(
        path=f"/sip-configs/{sip_id}",
        method="GET",
        headers=headers,
    )
    return result


@router.patch("/sip-configs/{sip_id}")
async def update_sip_config(
    sip_id: str,
    request: UpdateSipConfigRequest,
    req: Request,
    user: User = Depends(get_current_user)
):
    """Update a SIP configuration - proxied to Config Service."""
    headers = build_proxy_headers(req, user.workspace_id)
    result = await proxy_to_config(
        path=f"/sip-configs/{sip_id}",
        method="PATCH",
        headers=headers,
        json_body=request.model_dump(exclude_unset=True),
    )
    return result


@router.delete("/sip-configs/{sip_id}")
async def delete_sip_config(
    sip_id: str,
    req: Request,
    user: User = Depends(get_current_user)
):
    """Delete a SIP configuration - proxied to Config Service."""
    headers = build_proxy_headers(req, user.workspace_id)
    result = await proxy_to_config(
        path=f"/sip-configs/{sip_id}",
        method="DELETE",
        headers=headers,
    )
    return result
