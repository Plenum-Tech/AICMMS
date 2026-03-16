"""FastAPI dependency injection — shared dependencies for routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from cafm.api.auth import (
    ROLE_PERMISSIONS,
    TokenData,
    UserInfo,
    UserRole,
    decode_access_token,
)
from cafm.api.config import APIConfig
from cafm.core.config import AppConfig
from cafm.core.events import EventBus
from cafm.integration.manager import IntegrationManager

# ── Singletons managed by app lifespan ─────────────────────────────

_app_config: AppConfig | None = None
_api_config: APIConfig | None = None
_event_bus: EventBus | None = None
_integration_manager: IntegrationManager | None = None


def set_app_state(
    app_config: AppConfig,
    api_config: APIConfig,
    event_bus: EventBus,
    manager: IntegrationManager,
) -> None:
    """Called by app lifespan to initialize shared state."""
    global _app_config, _api_config, _event_bus, _integration_manager
    _app_config = app_config
    _api_config = api_config
    _event_bus = event_bus
    _integration_manager = manager


def clear_app_state() -> None:
    """Called on shutdown to clear references."""
    global _app_config, _api_config, _event_bus, _integration_manager
    _app_config = None
    _api_config = None
    _event_bus = None
    _integration_manager = None


# ── Config dependencies ────────────────────────────────────────────


def get_app_config() -> AppConfig:
    if _app_config is None:
        return AppConfig()
    return _app_config


def get_api_config() -> APIConfig:
    if _api_config is None:
        return APIConfig()
    return _api_config


def get_event_bus() -> EventBus:
    if _event_bus is None:
        return EventBus()
    return _event_bus


def get_integration_manager() -> IntegrationManager:
    if _integration_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integration manager not initialized",
        )
    return _integration_manager


# ── Auth dependencies ──────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    api_config: APIConfig = Depends(get_api_config),
) -> UserInfo:
    """Extract and validate the current user from the JWT token.

    For development, if no token is provided, returns a default admin user
    when debug mode is on.
    """
    if token is None:
        if api_config.debug:
            # Dev mode: return default admin for unauthenticated requests
            return UserInfo(
                user_id="dev-admin",
                username="admin",
                email="admin@aicmms.dev",
                role=UserRole.ADMIN,
                permissions=list(ROLE_PERMISSIONS[UserRole.ADMIN]),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data: TokenData = decode_access_token(token, api_config)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_perms = ROLE_PERMISSIONS.get(token_data.role, set())
    return UserInfo(
        user_id=token_data.sub,
        username=token_data.username,
        email=token_data.email,
        role=token_data.role,
        tenant_id=token_data.tenant_id,
        permissions=list(role_perms),
    )


def require_permission(permission: str):
    """Dependency factory — ensures the current user has a specific permission."""

    async def _check(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        role_perms = ROLE_PERMISSIONS.get(user.role, set())
        if permission not in role_perms and permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return user

    return _check


def require_role(*roles: UserRole):
    """Dependency factory — ensures the current user has one of the specified roles."""

    async def _check(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {', '.join(roles)}",
            )
        return user

    return _check


# ── Pagination dependency ──────────────────────────────────────────


class PaginationParams:
    """Common pagination parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


# ── Type aliases for clean route signatures ────────────────────────

CurrentUser = Annotated[UserInfo, Depends(get_current_user)]
Pagination = Annotated[PaginationParams, Depends()]
Manager = Annotated[IntegrationManager, Depends(get_integration_manager)]
Bus = Annotated[EventBus, Depends(get_event_bus)]
