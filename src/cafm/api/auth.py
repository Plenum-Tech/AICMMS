"""JWT authentication and role-based access control."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from cafm.api.config import APIConfig


class UserRole(StrEnum):
    """User roles for RBAC."""

    ADMIN = "admin"
    MANAGER = "manager"  # FM Manager
    TECHNICIAN = "technician"  # Field technician
    VIEWER = "viewer"  # Read-only dashboard user
    SYSTEM = "system"  # Internal service-to-service


class TokenData(BaseModel):
    """Decoded JWT token payload."""

    sub: str  # user_id
    username: str
    email: str | None = None
    role: UserRole = UserRole.VIEWER
    tenant_id: str | None = None  # Multi-tenancy support
    exp: datetime | None = None


class UserInfo(BaseModel):
    """Authenticated user information available in request context."""

    user_id: str
    username: str
    email: str | None = None
    role: UserRole = UserRole.VIEWER
    tenant_id: str | None = None
    permissions: list[str] = Field(default_factory=list)


# ── Role-based permission matrix ──────────────────────────────────

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.ADMIN: {
        "connectors:read", "connectors:write", "connectors:delete",
        "assets:read", "assets:write", "assets:delete",
        "work_orders:read", "work_orders:write", "work_orders:delete",
        "maintenance:read", "maintenance:write",
        "technicians:read", "technicians:write",
        "inspections:read", "inspections:write",
        "facilities:read", "facilities:write", "facilities:delete",
        "vendors:read", "vendors:write",
        "costs:read", "costs:write",
        "reports:read", "reports:write",
        "dashboard:read",
        "admin:manage",
    },
    UserRole.MANAGER: {
        "connectors:read",
        "assets:read", "assets:write",
        "work_orders:read", "work_orders:write",
        "maintenance:read", "maintenance:write",
        "technicians:read", "technicians:write",
        "inspections:read", "inspections:write",
        "facilities:read", "facilities:write",
        "vendors:read", "vendors:write",
        "costs:read", "costs:write",
        "reports:read", "reports:write",
        "dashboard:read",
    },
    UserRole.TECHNICIAN: {
        "assets:read",
        "work_orders:read", "work_orders:write",
        "inspections:read", "inspections:write",
        "technicians:read",
        "facilities:read",
        "dashboard:read",
    },
    UserRole.VIEWER: {
        "assets:read",
        "work_orders:read",
        "facilities:read",
        "dashboard:read",
        "reports:read",
    },
    UserRole.SYSTEM: {
        "connectors:read", "connectors:write", "connectors:delete",
        "assets:read", "assets:write", "assets:delete",
        "work_orders:read", "work_orders:write", "work_orders:delete",
        "maintenance:read", "maintenance:write",
        "technicians:read", "technicians:write",
        "inspections:read", "inspections:write",
        "facilities:read", "facilities:write", "facilities:delete",
        "vendors:read", "vendors:write",
        "costs:read", "costs:write",
        "reports:read", "reports:write",
        "dashboard:read",
        "admin:manage",
    },
}


def create_access_token(
    data: dict[str, Any],
    config: APIConfig | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    cfg = config or APIConfig()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=cfg.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, cfg.secret_key, algorithm=cfg.algorithm)


def decode_access_token(token: str, config: APIConfig | None = None) -> TokenData:
    """Decode and validate a JWT access token.

    Raises ``JWTError`` on invalid/expired tokens.
    """
    cfg = config or APIConfig()
    payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
    return TokenData(
        sub=payload.get("sub", ""),
        username=payload.get("username", ""),
        email=payload.get("email"),
        role=payload.get("role", UserRole.VIEWER),
        tenant_id=payload.get("tenant_id"),
        exp=payload.get("exp"),
    )


def has_permission(user: UserInfo, permission: str) -> bool:
    """Check if a user has a specific permission."""
    role_perms = ROLE_PERMISSIONS.get(user.role, set())
    return permission in role_perms or permission in user.permissions
