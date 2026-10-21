"""Exception hierarchy for the Telemetry Validation & Processing System.

Every error raised inside TVPS derives from :class:`TVPSError`.  The
exceptions carry structured information (code, field, context) so that a
failure can always be traced back to the input condition and the function
that produced it.  Nothing in this package swallows exceptions silently.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "TVPSError",
    "TelemetryParseError",
    "ValidationError",
    "ProcessingError",
    "SequenceOrderError",
]


class TVPSError(Exception):
    """Base class for all TVPS errors.

    Attributes:
        message: Human readable description of the failure.
        code: Stable machine readable error code (e.g. ``"PARSE_ERROR"``).
        field: Name of the telemetry field the error relates to, if any.
        context: Additional reproduction information (values, positions...).
    """

    default_code: str = "TVPS_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        field: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.field = field
        self.context: dict[str, Any] = dict(context or {})

    def to_dict(self) -> dict[str, Any]:
        """Return the error as a plain, JSON serialisable dictionary."""
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "context": dict(self.context),
        }

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


class TelemetryParseError(TVPSError):
    """Raised when a raw payload cannot be turned into a telemetry object."""

    default_code = "PARSE_ERROR"


class ValidationError(TVPSError):
    """Raised when telemetry does not satisfy the validation rules.

    ``details`` holds every individual validation failure so that a caller
    can report all problems of a packet at once instead of one per run.
    """

    default_code = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        field: str | None = None,
        context: dict[str, Any] | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message, code=code, field=field, context=context
        )
        self.details: list[dict[str, Any]] = list(details or [])

    def to_dict(self) -> dict[str, Any]:
        """Return the error and its individual details as a dictionary."""
        payload = super().to_dict()
        payload["details"] = [dict(detail) for detail in self.details]
        return payload


class ProcessingError(TVPSError):
    """Raised when telemetry cannot be processed into a normalised result."""

    default_code = "PROCESSING_ERROR"


class SequenceOrderError(ProcessingError):
    """Raised when a packet arrives with a sequence number that is not newer."""

    default_code = "SEQUENCE_ORDER_ERROR"
