"""Authentication API endpoints."""
from fastapi import APIRouter, HTTPException, status, Depends

from auth.models import (
    SignupRequest, LoginRequest, TokenResponse, RefreshRequest,
    UserResponse, CreateApiKeyRequest, ApiKeyResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from auth.service import AuthService
from auth.dependencies import get_current_user, require_auth
from auth.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=dict)
async def signup(request: SignupRequest):
    """
    Register a new user and create their workspace.
    
    Returns access and refresh tokens.
    """
    try:
        user, workspace, tokens = await AuthService.signup(request)
        return {
            "user": UserResponse(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                workspace_id=user.workspace_id,
                role=user.role,
                created_at=user.created_at,
            ).model_dump(),
            "workspace": {
                "workspace_id": workspace.workspace_id,
                "name": workspace.name,
            },
            "tokens": tokens.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=dict)
async def login(request: LoginRequest):
    """
    Login with email and password.
    
    Returns access and refresh tokens.
    """
    try:
        user, tokens = await AuthService.login(request)
        return {
            "user": UserResponse(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                workspace_id=user.workspace_id,
                role=user.role,
                created_at=user.created_at,
            ).model_dump(),
            "tokens": tokens.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    tokens = await AuthService.refresh_tokens(request.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: User = Depends(require_auth)):
    """
    Get current user profile.
    
    Requires authentication.
    """
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        workspace_id=user.workspace_id,
        role=user.role,
        created_at=user.created_at,
    )


# ============== API Keys ==============

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    request: CreateApiKeyRequest,
    user: User = Depends(require_auth)
):
    """
    Create a new API key.
    
    The full API key is only returned once on creation.
    Store it securely!
    """
    api_key, raw_key = await AuthService.create_api_key(user, request)
    return ApiKeyResponse(
        api_key_id=api_key.api_key_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        permissions=api_key.permissions,
        created_at=api_key.created_at,
        key=raw_key,  # Only returned on creation
    )


@router.get("/api-keys", response_model=list)
async def list_api_keys(user: User = Depends(require_auth)):
    """
    List all API keys for the current workspace.
    """
    keys = await AuthService.list_api_keys(user.workspace_id)
    return [
        ApiKeyResponse(
            api_key_id=key.api_key_id,
            name=key.name,
            key_prefix=key.key_prefix,
            permissions=key.permissions,
            created_at=key.created_at,
        ).model_dump()
        for key in keys
    ]


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    user: User = Depends(require_auth)
):
    """
    Delete (deactivate) an API key.
    """
    success = await AuthService.delete_api_key(api_key_id, user.workspace_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    return {"message": "API key deleted"}


# ============== Password Reset ==============

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset email.
    
    Note: For security, always returns success even if email doesn't exist.
    """
    # TODO: Implement email sending
    # For now, just return success
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using token from email.
    """
    # TODO: Implement password reset
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented",
    )
