"""
HTTP Proxy utilities for Gateway to communicate with downstream services.
This enables proper microservice architecture where Gateway routes to:
- Analytics Service (8001): Calls, Analysis, Webhooks
- Orchestration Service (8003): Campaigns, Job Queue
- Config Service (8002): Assistants, SIP, Phone Numbers
"""
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request

logger = logging.getLogger("gateway.proxy")

# Service URLs (container-to-container communication)
ANALYTICS_SERVICE_URL = "http://analytics:8001"
ORCHESTRATION_SERVICE_URL = "http://orchestration:8003"
CONFIG_SERVICE_URL = "http://config:8002"


async def proxy_request(
    service_url: str,
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Proxy a request to a downstream service.
    
    Args:
        service_url: Base URL of the target service
        path: API path (e.g., "/calls/123")
        method: HTTP method (GET, POST, PATCH, DELETE)
        headers: Optional headers to forward (auth, etc.)
        json_body: Optional JSON request body
        query_params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        JSON response from the downstream service
        
    Raises:
        HTTPException: If the downstream service returns an error
    """
    url = f"{service_url}{path}"
    
    # Clean up headers - remove host and content-length
    clean_headers = {}
    if headers:
        for key, value in headers.items():
            if key.lower() not in ['host', 'content-length']:
                clean_headers[key] = value
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=clean_headers,
                json=json_body,
                params=query_params,
            )
            
            # Log the proxy request
            logger.debug(f"Proxied {method} {url} -> {response.status_code}")
            
            # Handle error responses
            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                    
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail,
                )
            
            # Return JSON response
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"data": response.text}
                
    except httpx.TimeoutException:
        logger.error(f"Timeout proxying to {url}")
        raise HTTPException(status_code=504, detail="Downstream service timeout")
    except httpx.ConnectError:
        logger.error(f"Connection error proxying to {url}")
        raise HTTPException(status_code=503, detail="Downstream service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


def extract_auth_headers(request: Request) -> Dict[str, str]:
    """Extract authorization headers from the incoming request to forward downstream."""
    headers = {}
    
    # Forward Authorization header (Bearer token)
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]
    
    # Forward X-API-Key header
    if "x-api-key" in request.headers:
        headers["X-API-Key"] = request.headers["x-api-key"]
        
    return headers


def build_proxy_headers(request: Request, workspace_id: Optional[str] = None) -> Dict[str, str]:
    """
    Build headers for proxy request including auth and workspace context.
    
    Args:
        request: The incoming FastAPI request
        workspace_id: Optional workspace ID to include (for multi-tenancy)
    """
    headers = extract_auth_headers(request)
    
    # Add workspace context for downstream services
    if workspace_id:
        headers["X-Workspace-ID"] = workspace_id
        
    return headers


# Convenience functions for each service
async def proxy_to_analytics(
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Proxy request to Analytics Service (8001)."""
    return await proxy_request(
        ANALYTICS_SERVICE_URL,
        path,
        method,
        headers,
        json_body,
        query_params,
    )


async def proxy_to_orchestration(
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Proxy request to Orchestration Service (8003)."""
    return await proxy_request(
        ORCHESTRATION_SERVICE_URL,
        path,
        method,
        headers,
        json_body,
        query_params,
    )


async def proxy_to_config(
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Proxy request to Config Service (8002)."""
    return await proxy_request(
        CONFIG_SERVICE_URL,
        path,
        method,
        headers,
        json_body,
        query_params,
    )
