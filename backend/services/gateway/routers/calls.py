"""Calls API endpoints with multi-tenancy support."""
import logging
from fastapi import APIRouter, Request, Response

from services.gateway.proxy import proxy_to_analytics
from shared.settings import config

logger = logging.getLogger("api.calls")
router = APIRouter()

# Proxy all call-related endpoints to Analytics Service

async def forward_to_analytics(request: Request, path: str):
    """Helper to forward request to analytics service."""
    try:
        json_body = await request.json()
    except:
        json_body = None
        
    return await proxy_to_analytics(
        path=path,
        method=request.method,
        headers=dict(request.headers),
        query_params=dict(request.query_params),
        json_body=json_body
    )

@router.post("/calls")
async def create_call(request: Request):
    return await forward_to_analytics(request, "/calls")

@router.get("/calls")
async def list_calls(request: Request):
    return await forward_to_analytics(request, "/calls")

@router.get("/calls/{call_id}")
async def get_call(call_id: str, request: Request):
    return await forward_to_analytics(request, f"/calls/{call_id}")

@router.get("/calls/{call_id}/analysis")
async def get_call_analysis(call_id: str, request: Request):
    return await forward_to_analytics(request, f"/calls/{call_id}/analysis")

@router.post("/calls/{call_id}/analyze")
async def trigger_analysis(call_id: str, request: Request):
    return await forward_to_analytics(request, f"/calls/{call_id}/analyze")

@router.get("/analytics/calls")
async def get_call_analytics(request: Request):
    return await forward_to_analytics(request, "/analytics/calls")

@router.get("/analytics/summary")
async def get_analytics_summary(request: Request):
    return await forward_to_analytics(request, "/analytics/summary")

