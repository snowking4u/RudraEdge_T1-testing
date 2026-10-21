"""Processing of validated telemetry into normalised results.

The processor converts a validated telemetry packet into the normalised
structure required by REQ-007 and detects packets that arrive out of order
(REQ-005).  An out-of-order packet is rejected with a visible error; it is
never silently discarded.
"""

from __future__ import annotations

from typing import Any, Mapping

from .errors import SequenceOrderError, ValidationError
from .models import (
    STATUS_OUT_OF_ORDER,
    STATUS_PROCESSED,
    Result,
    make_error_detail,
    make_result,
    result_from_error,
)
from .validator import validate_or_raise

__all__ = ["process_telemetry", "TelemetryProcessor", "normalise_telemetry"]


def normalise_telemetry(data: Mapping[str, Any]) -> dict[str, Any]:
    """Build the normalised representation of a validated telemetry packet.

    Args:
        data: A telemetry packet that already passed validation.

    Returns:
        The normalised telemetry dictionary (REQ-007).
    """
    return {
        "sequence": int(data["sequence"]),
        "timestamp": str(data["timestamp"]),
        "position": {
            "latitude": float(data["latitude"]),
            "longitude": float(data["longitude"]),
        },
        "altitude": float(data["altitude"]),
        "speed": float(data["speed"]),
        "battery": float(data["battery"]),
        "satellites": int(data["satellites"]),
        "status": STATUS_PROCESSED,
    }


def process_telemetry(
    data: Mapping[str, Any] | Any,
    last_sequence: int | None = None,
) -> Result:
    """Process one telemetry packet into a normalised result.

    Args:
        data: Telemetry packet (decoded object).  The packet is validated
            again before processing, so the function is safe to call
            directly from a test.
        last_sequence: Sequence number of the last successfully processed
            packet.  When given, a packet whose sequence is not strictly
            greater is rejected as out of order (REQ-005).  ``None``
            disables the ordering check because no history is available.

    Returns:
        A result envelope.  ``status`` is ``"PROCESSED"`` on success and
        ``"REJECTED"`` when the packet is invalid or out of order.
    """
    try:
        validated = validate_or_raise(data)
    except ValidationError as exc:
        return result_from_error(exc)

    sequence = int(validated["sequence"])
    if last_sequence is not None and sequence <= last_sequence:
        error = SequenceOrderError(
            f"sequence {sequence} is out of order, expected greater than {last_sequence}",
            field="sequence",
            context={"sequence": sequence, "last_sequence": last_sequence},
        )
        detail = make_error_detail(
            error.code, error.message, field=error.field, context=error.context
        )
        return make_result(
            status=STATUS_OUT_OF_ORDER,
            errors=[detail["message"]],
            error_details=[detail],
        )

    return make_result(status=STATUS_PROCESSED, data=normalise_telemetry(validated))


class TelemetryProcessor:
    """Stateful processor that remembers the last processed sequence number.

    The processor is used by the batch and service layer to detect packets
    that arrive out of order.  It is deliberately explicit about its state
    so that tests can construct a processor with a known history.
    """

    def __init__(self, last_sequence: int | None = None) -> None:
        """Create a processor, optionally seeded with a known history."""
        self.last_sequence: int | None = last_sequence

    def process(self, data: Mapping[str, Any] | Any) -> Result:
        """Process one packet and update the sequence history on success.

        A rejected packet (invalid or out of order) does not change the
        stored sequence number.
        """
        result = process_telemetry(data, self.last_sequence)
        if result["valid"] and result["status"] == STATUS_PROCESSED:
            assert result["data"] is not None  # narrowed for type checkers
            self.last_sequence = int(result["data"]["sequence"])
        return result
