"""Raw payload parsing for TVPS.

The parser is the only module that touches raw text.  It converts a JSON
payload into a plain telemetry dictionary and reports malformed input as a
structured rejection instead of raising an unhandled exception.
"""

from __future__ import annotations

import json
from typing import Any

from .errors import TelemetryParseError
from .models import (
    STATUS_PARSED,
    STATUS_REJECTED,
    Result,
    make_error_detail,
    make_result,
)

__all__ = ["parse_telemetry"]


def parse_telemetry(raw_json: str | bytes | bytearray | None) -> Result:
    """Parse a raw telemetry payload.

    Args:
        raw_json: JSON text (or UTF-8 encoded bytes) describing one
            telemetry packet.  ``None`` is accepted and reported as an
            error so that callers never have to pre-check the input.

    Returns:
        A result envelope.  On success ``status`` is ``"PARSED"`` and
        ``data`` holds the decoded telemetry object.  On failure ``valid``
        is ``False`` and ``errors`` explains why.

    Example:
        >>> parse_telemetry('{"sequence": 1}')["status"]
        'PARSED'
        >>> parse_telemetry('{"sequence": ')["errors"]
        ['malformed JSON: Expecting value (line 1, column 14)']
    """
    try:
        payload = _decode_payload(raw_json)
    except TelemetryParseError as exc:
        detail = make_error_detail(
            exc.code, exc.message, field=exc.field, context=exc.context
        )
        return make_result(
            status=STATUS_REJECTED, errors=[detail["message"]], error_details=[detail]
        )
    return make_result(status=STATUS_PARSED, data=payload)


def _decode_payload(raw_json: str | bytes | bytearray | None) -> dict[str, Any]:
    """Decode ``raw_json`` into a telemetry object or raise ``TelemetryParseError``."""
    if raw_json is None:
        raise TelemetryParseError(
            "telemetry input must not be None",
            code="EMPTY_INPUT",
        )

    if isinstance(raw_json, (bytes, bytearray)):
        try:
            text = bytes(raw_json).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TelemetryParseError(
                f"telemetry input is not valid UTF-8: {exc.reason}",
                code="PARSE_ERROR",
                context={"reason": exc.reason, "position": exc.start},
            ) from exc
    elif isinstance(raw_json, str):
        text = raw_json
    else:
        raise TelemetryParseError(
            "telemetry input must be a string or bytes, got "
            f"{type(raw_json).__name__}",
            code="PARSE_ERROR",
            context={"input_type": type(raw_json).__name__},
        )

    if not text.strip():
        raise TelemetryParseError(
            "telemetry input must not be empty",
            code="EMPTY_INPUT",
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TelemetryParseError(
            f"malformed JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})",
            code="PARSE_ERROR",
            context={
                "reason": exc.msg,
                "line": exc.lineno,
                "column": exc.colno,
                "position": exc.pos,
            },
        ) from exc

    if not isinstance(payload, dict):
        raise TelemetryParseError(
            f"telemetry JSON must be an object, got {type(payload).__name__}",
            code="PARSE_ERROR",
            context={"decoded_type": type(payload).__name__},
        )

    return payload
