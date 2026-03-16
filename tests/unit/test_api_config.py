"""Tests for API configuration and auth."""

from __future__ import annotations

from datetime import timedelta

import pytest

from cafm.api.auth import (
    ROLE_PERMISSIONS,
    UserInfo,
    UserRole,
    create_access_token,
    decode_access_token,
    has_permission,
)
from cafm.api.config import APIConfig


class TestAPIConfig:
    """Tests for API configuration."""

    def test_default_values(self):
        config = APIConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 480
        assert config.rate_limit_per_minute == 120
        assert config.default_page_size == 50
        assert config.max_page_size == 500

    def test_cors_defaults(self):
        config = APIConfig()
        assert "*" in config.cors_origins
        assert config.cors_allow_credentials is True


class TestAuth:
    """Tests for JWT auth and RBAC."""

    def test_create_and_decode_token(self):
        config = APIConfig(secret_key="test-secret")
        token = create_access_token(
            data={
                "sub": "user-001",
                "username": "testuser",
                "email": "test@example.com",
                "role": "admin",
            },
            config=config,
        )
        assert isinstance(token, str)

        decoded = decode_access_token(token, config)
        assert decoded.sub == "user-001"
        assert decoded.username == "testuser"
        assert decoded.email == "test@example.com"
        assert decoded.role == UserRole.ADMIN

    def test_token_with_custom_expiry(self):
        config = APIConfig(secret_key="test-secret")
        token = create_access_token(
            data={"sub": "user-002", "username": "short"},
            config=config,
            expires_delta=timedelta(minutes=5),
        )
        decoded = decode_access_token(token, config)
        assert decoded.sub == "user-002"

    def test_expired_token_raises(self):
        from jose import JWTError
        config = APIConfig(secret_key="test-secret")
        token = create_access_token(
            data={"sub": "user-003", "username": "expired"},
            config=config,
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(JWTError):
            decode_access_token(token, config)

    def test_invalid_token_raises(self):
        from jose import JWTError
        config = APIConfig(secret_key="test-secret")
        with pytest.raises(JWTError):
            decode_access_token("invalid.token.here", config)


class TestRBAC:
    """Tests for role-based access control."""

    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert "connectors:write" in admin_perms
        assert "assets:delete" in admin_perms
        assert "admin:manage" in admin_perms

    def test_viewer_has_limited_permissions(self):
        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert "assets:read" in viewer_perms
        assert "dashboard:read" in viewer_perms
        assert "assets:write" not in viewer_perms
        assert "admin:manage" not in viewer_perms

    def test_technician_permissions(self):
        tech_perms = ROLE_PERMISSIONS[UserRole.TECHNICIAN]
        assert "work_orders:write" in tech_perms
        assert "inspections:write" in tech_perms
        assert "connectors:write" not in tech_perms

    def test_has_permission_check(self):
        admin = UserInfo(
            user_id="u1", username="admin", role=UserRole.ADMIN
        )
        assert has_permission(admin, "admin:manage") is True
        assert has_permission(admin, "connectors:delete") is True

        viewer = UserInfo(
            user_id="u2", username="viewer", role=UserRole.VIEWER
        )
        assert has_permission(viewer, "admin:manage") is False
        assert has_permission(viewer, "assets:read") is True

    def test_user_roles_are_str_enum(self):
        assert UserRole.ADMIN == "admin"
        assert UserRole.TECHNICIAN == "technician"

    def test_all_roles_have_permissions(self):
        for role in UserRole:
            assert role in ROLE_PERMISSIONS
            assert len(ROLE_PERMISSIONS[role]) > 0
