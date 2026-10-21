"""Validation rules for telemetry packets.

The validator checks every mandatory field of a telemetry packet:

1. presence (REQ-002);
2. data type (REQ-003);
3. value range including the boundary values (REQ-004);
4. sequence number semantics (REQ-005).

All failures of a packet are collected so that a report lists every
problem of a packet, not only the first one.  The order of the reported
errors is deterministic (fields are checked in :data:`FIELD_SPECS` order).
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from .errors import ValidationError
from .models import (
    FIELD_SPECS,
    STATUS_REJECTED,
    STATUS_VALIDATED,
    ErrorDetail,
    FieldKind,
    FieldSpec,
    Result,
    make_error_detail,
    make_result,
)

__all__ = [
    "collect_validation_errors",
    "validate_telemetry",
    "validate_or_raise",
]


def validate_telemetry(data: Mapping[str, Any] | Any) -> Result:
    """Validate a telemetry packet.

    Args:
        data: Decoded telemetry object (as produced by the parser).

    Returns:
        A result envelope.  On success ``status`` is ``"VALIDATED"`` and
        ``data`` holds a copy of the accepted packet.  On failure ``valid``
        is ``False`` and ``errors`` contains one message per problem.

    Example:
        >>> validate_telemetry({"sequence": "one"})["valid"]
        False
    """
    details = collect_validation_errors(data)
    if details:
        return make_result(
            status=STATUS_REJECTED,
            errors=[detail["message"] for detail in details],
            error_details=details,
        )
    return make_result(status=STATUS_VALIDATED, data=dict(data))


def validate_or_raise(data: Mapping[str, Any] | Any) -> dict[str, Any]:
    """Validate a packet and raise :class:`ValidationError` when it is invalid.

    This is the strict variant used by the processor, which must never
    work with unvalidated telemetry.

    Raises:
        ValidationError: If the packet violates any validation rule.
    """
    details = collect_validation_errors(data)
    if details:
        first = details[0]
        raise ValidationError(
            first["message"],
            code=first["code"],
            field=first["field"],
            context=first["context"],
            details=details,
        )
    return dict(data)


def collect_validation_errors(data: Mapping[str, Any] | Any) -> list[ErrorDetail]:
    """Return every validation failure of ``data`` (empty list when valid)."""
    if not isinstance(data, Mapping):
        return [
            make_error_detail(
                "INVALID_PAYLOAD",
                f"telemetry data must be a JSON object, got {type(data).__name__}",
                context={"payload_type": type(data).__name__},
            )
        ]

    details: list[ErrorDetail] = []
    for spec in FIELD_SPECS.values():
        if spec.name not in data:
            details.append(_missing_field_detail(spec))
            continue
        value = data[spec.name]
        type_error = _check_type(spec, value)
        if type_error is not None:
            details.append(type_error)
            continue
        range_error = _check_range(spec, value)
        if range_error is not None:
            details.append(range_error)
    return details


def _missing_field_detail(spec: FieldSpec) -> ErrorDetail:
    """Build the detail used when a mandatory field is absent."""
    return make_error_detail(
        "MISSING_FIELD",
        f"{spec.name} field is required",
        field=spec.name,
        context={"mandatory_field": spec.name},
    )


def _check_type(spec: FieldSpec, value: Any) -> ErrorDetail | None:
    """Return a type error detail when ``value`` does not match ``spec``."""
    if spec.kind is FieldKind.STRING:
        if not isinstance(value, str):
            return _type_error(spec, value)
        if not value.strip():
            return make_error_detail(
                "INVALID_VALUE",
                f"{spec.name} must be a non-empty string",
                field=spec.name,
                context={"value": value},
            )
        return None

    if spec.kind is FieldKind.INTEGER:
        # ``bool`` is a subclass of ``int`` and is not accepted as a number.
        if isinstance(value, bool) or not isinstance(value, int):
            return _type_error(spec, value)
        return None

    # FieldKind.NUMBER
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return _type_error(spec, value)
    return None


def _type_error(spec: FieldSpec, value: Any) -> ErrorDetail:
    """Build the detail used when a field carries the wrong data type."""
    return make_error_detail(
        "INVALID_TYPE",
        f"{spec.name} must be {spec.type_message}",
        field=spec.name,
        context={
            "expected_type": spec.type_message,
            "actual_type": type(value).__name__,
            "value": repr(value),
        },
    )


def _check_range(spec: FieldSpec, value: Any) -> ErrorDetail | None:
    """Return a range error detail when ``value`` is outside the allowed range."""
    if spec.minimum is None and spec.maximum is None:
        return None

    if isinstance(value, float) and not math.isfinite(value):
        # NaN and +/-inf are never inside a closed range.
        return make_error_detail(
            "OUT_OF_RANGE",
            _range_message(spec),
            field=spec.name,
            context={"value": repr(value), "reason": "value is not finite"},
        )

    if spec.minimum is not None and value < spec.minimum:
        return make_error_detail(
            "OUT_OF_RANGE",
            _range_message(spec),
            field=spec.name,
            context={
                "value": value,
                "minimum": spec.minimum,
                "maximum": spec.maximum,
            },
        )

    if spec.maximum is not None and value > spec.maximum:
        return make_error_detail(
            "OUT_OF_RANGE",
            _range_message(spec),
            field=spec.name,
            context={
                "value": value,
                "minimum": spec.minimum,
                "maximum": spec.maximum,
            },
        )

    return None


def _range_message(spec: FieldSpec) -> str:
    """Return the human readable range message of ``spec``."""
    if spec.range_message:
        return spec.range_message
    if spec.maximum is None:
        return f"{spec.name} must be greater than {spec.minimum}"
    return f"{spec.name} must be between {spec.minimum} and {spec.maximum}"
