"""Authentication routes — token generation and user info."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from cafm.api.auth import (
    ROLE_PERMISSIONS,
    UserRole,
    create_access_token,
)
from cafm.api.config import APIConfig
from cafm.api.dependencies import CurrentUser, get_api_config
from cafm.api.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# In production, this would check against a user database.
# For now, a simple dev-mode user store.
DEV_USERS: dict[str, dict] = {
    "admin": {
        "user_id": "user-001",
        "username": "admin",
        "password": "admin",
        "email": "admin@aicmms.dev",
        "role": UserRole.ADMIN,
    },
    "manager": {
        "user_id": "user-002",
        "username": "manager",
        "password": "manager",
        "email": "manager@aicmms.dev",
        "role": UserRole.MANAGER,
    },
    "technician": {
        "user_id": "user-003",
        "username": "technician",
        "password": "technician",
        "email": "tech@aicmms.dev",
        "role": UserRole.TECHNICIAN,
    },
    "viewer": {
        "user_id": "user-004",
        "username": "viewer",
        "password": "viewer",
        "email": "viewer@aicmms.dev",
        "role": UserRole.VIEWER,
    },
}


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    api_config: APIConfig = Depends(get_api_config),
):
    """Authenticate and return a JWT access token."""
    user = DEV_USERS.get(form_data.username)
    if user is None or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={
            "sub": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        },
        config=api_config,
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user_info(user: CurrentUser):
    """Get the currently authenticated user's information."""
    return APIResponse(
        data={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions,
            "tenant_id": user.tenant_id,
        }
    )


@router.get("/roles")
async def list_roles():
    """List all available roles and their permissions."""
    return APIResponse(
        data={
            role.value: sorted(perms)
            for role, perms in ROLE_PERMISSIONS.items()
        }
    )
