"""Tests for API middleware."""

from __future__ import annotations

import pytest

from cafm.api.middleware import cafm_error_to_status
from cafm.core.exceptions import (
    AuthenticationError,
    CAFMError,
    ConfigurationError,
    ConnectorError,
    ConnectorNotFoundError,
    DataError,
    IntegrationError,
    SchemaError,
)


class TestExceptionMapping:
    """Tests for CAFMError → HTTP status code mapping."""

    def test_not_found_error(self):
        exc = ConnectorNotFoundError("PostgreSQL connector not found")
        assert cafm_error_to_status(exc) == 404

    def test_auth_error(self):
        exc = AuthenticationError("Invalid credentials")
        assert cafm_error_to_status(exc) == 401

    def test_schema_error(self):
        exc = SchemaError("Invalid schema")
        assert cafm_error_to_status(exc) == 422

    def test_config_error(self):
        exc = ConfigurationError("Missing setting")
        assert cafm_error_to_status(exc) == 400

    def test_data_error(self):
        exc = DataError("Invalid data")
        assert cafm_error_to_status(exc) == 400

    def test_connector_error(self):
        exc = ConnectorError("Connection failed")
        assert cafm_error_to_status(exc) == 502

    def test_integration_error(self):
        exc = IntegrationError("Pipeline failed")
        assert cafm_error_to_status(exc) == 500

    def test_base_cafm_error(self):
        exc = CAFMError("Generic error")
        assert cafm_error_to_status(exc) == 500
