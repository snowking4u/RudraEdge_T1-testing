"""Shared data model for TVPS: field specifications and result envelopes.

The module is intentionally free of I/O and business logic.  It defines:

* the telemetry field specifications (mandatory fields, types, ranges);
* the single result envelope used by *every* TVPS module;
* small helpers used to build that envelope consistently.

Keeping one envelope for parser, validator, processor and service is a hard
requirement of the system: results are never mixed between modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, TypedDict

from .errors import TVPSError, ValidationError

__all__ = [
    "FieldKind",
    "FieldSpec",
    "FIELD_SPECS",
    "MANDATORY_FIELDS",
    "ErrorDetail",
    "BatchErrorDetail",
    "Result",
    "STATUS_PARSED",
    "STATUS_VALIDATED",
    "STATUS_PROCESSED",
    "STATUS_REJECTED",
    "STATUS_PARTIAL",
    "STATUS_OUT_OF_ORDER",
    "make_error_detail",
    "make_result",
    "result_from_error",
]


class FieldKind(Enum):
    """Allowed data kinds for a telemetry field."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"


@dataclass(frozen=True)
class FieldSpec:
    """Definition of a single mandatory telemetry field.

    Attributes:
        name: Field name as it appears in the telemetry packet.
        kind: Expected data kind.
        minimum: Lower bound of the accepted range (inclusive).
        maximum: Upper bound of the accepted range (inclusive).
        type_message: Human readable expectation used in error messages.
        range_message: Optional override for the range error message.
    """

    name: str
    kind: FieldKind
    minimum: float | None = None
    maximum: float | None = None
    type_message: str = ""
    range_message: str | None = None


#: Specification of every mandatory telemetry field, in report order.
FIELD_SPECS: Final[dict[str, FieldSpec]] = {
    "timestamp": FieldSpec(
        name="timestamp",
        kind=FieldKind.STRING,
        type_message="a non-empty string",
    ),
    "sequence": FieldSpec(
        name="sequence",
        kind=FieldKind.INTEGER,
        minimum=1,
        type_message="an integer",
        range_message="sequence must be a positive integer",
    ),
    "latitude": FieldSpec(
        name="latitude",
        kind=FieldKind.NUMBER,
        minimum=-90,
        maximum=90,
        type_message="a number",
    ),
    "longitude": FieldSpec(
        name="longitude",
        kind=FieldKind.NUMBER,
        minimum=-180,
        maximum=180,
        type_message="a number",
    ),
    "altitude": FieldSpec(
        name="altitude",
        kind=FieldKind.NUMBER,
        minimum=0,
        maximum=10000,
        type_message="a number",
    ),
    "speed": FieldSpec(
        name="speed",
        kind=FieldKind.NUMBER,
        minimum=0,
        maximum=500,
        type_message="a number",
    ),
    "battery": FieldSpec(
        name="battery",
        kind=FieldKind.NUMBER,
        minimum=0,
        maximum=100,
        type_message="a number",
    ),
    "satellites": FieldSpec(
        name="satellites",
        kind=FieldKind.INTEGER,
        minimum=0,
        maximum=40,
        type_message="an integer",
    ),
}

#: Ordered list of the mandatory telemetry fields.
MANDATORY_FIELDS: Final[tuple[str, ...]] = tuple(FIELD_SPECS.keys())

# --------------------------------------------------------------------------
# Result envelope
# --------------------------------------------------------------------------

#: Status code: payload was parsed into a telemetry object.
STATUS_PARSED: Final[str] = "PARSED"
#: Status code: telemetry passed validation.
STATUS_VALIDATED: Final[str] = "VALIDATED"
#: Status code: telemetry was normalised and processed.
STATUS_PROCESSED: Final[str] = "PROCESSED"
#: Status code: the input was rejected (parse or validation failure).
STATUS_REJECTED: Final[str] = "REJECTED"
#: Status code: a batch where only part of the input was acceptable.
STATUS_PARTIAL: Final[str] = "PARTIAL"
#: Status code: the packet was rejected because it arrived out of order.
STATUS_OUT_OF_ORDER: Final[str] = "OUT_OF_ORDER"


class ErrorDetail(TypedDict):
    """Structured description of a single failure."""

    code: str
    field: str | None
    message: str
    context: dict[str, Any]


class BatchErrorDetail(ErrorDetail):
    """Error detail of a batch entry, enriched with the packet position.

    Attributes:
        index: Position of the failing packet inside the batch.
        status: Status of the failing packet.
    """

    index: int
    status: str


class Result(TypedDict):
    """The single result envelope returned by every TVPS public function.

    Attributes:
        valid: ``True`` when the operation completed without any error.
        errors: Human readable error messages (empty when valid).
        error_details: Structured counterpart of ``errors``.
        status: One of the ``STATUS_*`` constants.
        data: Operation payload (``None`` when the operation failed).
    """

    valid: bool
    errors: list[str]
    error_details: list[ErrorDetail]
    status: str
    data: dict[str, Any] | None


def make_error_detail(
    code: str,
    message: str,
    *,
    field: str | None = None,
    context: dict[str, Any] | None = None,
) -> ErrorDetail:
    """Build a single structured error detail."""
    return {
        "code": code,
        "field": field,
        "message": message,
        "context": dict(context or {}),
    }


def make_result(
    *,
    status: str,
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    error_details: list[ErrorDetail] | None = None,
) -> Result:
    """Build a result envelope.

    The envelope always carries the same keys, independently of the module
    that produced it.  ``valid`` is derived from the presence of errors so
    that it can never contradict ``errors``.
    """
    details = list(error_details or [])
    messages = list(errors) if errors is not None else [d["message"] for d in details]
    return {
        "valid": not messages,
        "errors": messages,
        "error_details": details,
        "status": status,
        "data": data,
    }


def result_from_error(
    error: BaseException,
    *,
    status: str = STATUS_REJECTED,
    extra_context: dict[str, Any] | None = None,
) -> Result:
    """Convert an exception into a result envelope.

    The exception is never hidden: its type, message and (for unexpected
    errors) any extra context such as a traceback are kept inside the error
    details so the failure remains observable and reproducible.
    """
    if isinstance(error, ValidationError) and error.details:
        details = [dict(detail) for detail in error.details]
    elif isinstance(error, TVPSError):
        details = [make_error_detail(error.code, error.message, field=error.field, context=error.context)]
    else:
        context = {
            "exception_type": type(error).__name__,
            "exception_message": str(error),
        }
        context.update(extra_context or {})
        details = [
            make_error_detail(
                "UNEXPECTED_ERROR",
                f"{type(error).__name__}: {error}",
                context=context,
            )
        ]
    return make_result(status=status, errors=[d["message"] for d in details], error_details=details)
