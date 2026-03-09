"""Exception hierarchy for the CAFM platform."""

from __future__ import annotations


class CAFMError(Exception):
    """Base exception for all CAFM platform errors."""


# ── Connector errors ──────────────────────────────────────────────


class ConnectorError(CAFMError):
    """Base for connector-related errors."""


class ConnectionError(ConnectorError):
    """Failed to establish or maintain a connection."""


class AuthenticationError(ConnectorError):
    """Invalid credentials or permission denied."""


class ConnectorNotFoundError(ConnectorError):
    """Requested connector type is not registered."""


class ConnectorAlreadyRegisteredError(ConnectorError):
    """Attempted to register a connector type that already exists."""


# ── Schema errors ─────────────────────────────────────────────────


class SchemaError(CAFMError):
    """Base for schema-related errors."""


class SchemaDiscoveryError(SchemaError):
    """Failed to discover schema from a data source."""


class SchemaValidationError(SchemaError):
    """Schema data is invalid or inconsistent."""


# ── Data errors ───────────────────────────────────────────────────


class DataError(CAFMError):
    """Base for data access and manipulation errors."""


class QueryError(DataError):
    """A query failed to execute."""


class MappingError(DataError):
    """Field mapping between source and unified model failed."""


# ── Integration errors ────────────────────────────────────────────


class IntegrationError(CAFMError):
    """Base for integration/pipeline errors."""


class PipelineError(IntegrationError):
    """A pipeline step failed."""


class TransformError(IntegrationError):
    """A data transformation failed."""


# ── Configuration errors ──────────────────────────────────────────


class ConfigurationError(CAFMError):
    """Invalid or missing configuration."""
