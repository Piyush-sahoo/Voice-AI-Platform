"""Authentication models."""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
import secrets


def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{secrets.token_hex(6)}"


# ============== Database Models ==============

class User(BaseModel):
    """User model."""
    user_id: str = Field(default_factory=lambda: generate_id("user"))
    email: EmailStr
    password_hash: str
    name: str
    workspace_id: str
    role: str = "owner"  # owner, admin, member
    email_verified: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Workspace(BaseModel):
    """Workspace model for multi-tenancy."""
    workspace_id: str = Field(default_factory=lambda: generate_id("ws"))
    name: str
    owner_id: str
    plan: str = "free"  # free, starter, pro, enterprise
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiKey(BaseModel):
    """API Key for programmatic access."""
    api_key_id: str = Field(default_factory=lambda: generate_id("ak"))
    key_hash: str  # Hashed API key
    key_prefix: str  # First 8 chars for identification (e.g., "vk_abc123...")
    name: str
    workspace_id: str
    user_id: str
    permissions: List[str] = Field(default_factory=lambda: ["*"])  # ["calls:read", "calls:write", etc.]
    last_used: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RefreshToken(BaseModel):
    """Refresh token for JWT renewal."""
    token_id: str = Field(default_factory=lambda: generate_id("rt"))
    token_hash: str
    user_id: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============== Request/Response Models ==============

class SignupRequest(BaseModel):
    """Signup request."""
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    workspace_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response after login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response (public data only)."""
    user_id: str
    email: str
    name: str
    workspace_id: str
    role: str
    created_at: datetime


class CreateApiKeyRequest(BaseModel):
    """Create API key request."""
    name: str = Field(min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=lambda: ["*"])


class ApiKeyResponse(BaseModel):
    """API key response (includes full key only on creation)."""
    api_key_id: str
    name: str
    key_prefix: str
    permissions: List[str]
    created_at: datetime
    key: Optional[str] = None  # Full key only returned on creation


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    token: str
    new_password: str = Field(min_length=8)
