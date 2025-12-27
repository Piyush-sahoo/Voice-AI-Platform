"""FastAPI dependencies for authentication."""
import os
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User
from .service import AuthService

# Auth enabled flag
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[User]:
    """
    Get the current authenticated user.
    
    Supports two auth methods:
    1. Bearer token (JWT) - For dashboard/frontend
    2. X-API-Key header - For programmatic API access
    
    Returns None if AUTH_ENABLED is False.
    """
    # If auth is disabled, return None (all requests allowed)
    if not AUTH_ENABLED:
        return None
    
    # Try API Key first
    if x_api_key:
        result = await AuthService.get_user_from_api_key(x_api_key)
        if result:
            user, _ = result
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Try Bearer token
    if credentials:
        user = await AuthService.get_user_from_token(credentials.credentials)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # No credentials provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    Does not raise an error if not authenticated.
    """
    if not AUTH_ENABLED:
        return None
    
    # Try API Key
    if x_api_key:
        result = await AuthService.get_user_from_api_key(x_api_key)
        if result:
            user, _ = result
            return user
        return None
    
    # Try Bearer token
    if credentials:
        return await AuthService.get_user_from_token(credentials.credentials)
    
    return None


async def get_workspace_id(
    user: Optional[User] = Depends(get_current_user),
) -> Optional[str]:
    """
    Get the workspace ID from the current user.
    Returns None if auth is disabled.
    """
    if user:
        return user.workspace_id
    return None


def require_auth(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Dependency that requires authentication.
    Raises 401 if not authenticated (even if AUTH_ENABLED is False).
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user
