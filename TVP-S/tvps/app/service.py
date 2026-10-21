"""Application service layer for TVPS.

The service wires the individual stages together and offers the entry points
that are used by the demo program and by the verification suite:

* :func:`process_packet` - full pipeline for a single raw packet;
* :func:`process_batch` - full pipeline for a list of packets;
* :func:`handle_validation_error` - turns an error into an observable result;
* :func:`load_cases` / :func:`load_raw_packets` - deterministic data loading.

The service never hides a failure: every rejected input is reported through
the result envelope, and unexpected exceptions are converted into a visible
error result that keeps the exception type and traceback.
"""

from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import TVPSError, ValidationError
from .models import (
    STATUS_PARTIAL,
    STATUS_PROCESSED,
    STATUS_REJECTED,
    BatchErrorDetail,
    Result,
    make_error_detail,
    make_result,
    result_from_error,
)
from .parser import parse_telemetry
from .processor import TelemetryProcessor
from .validator import validate_telemetry

__all__ = [
    "DATA_DIR",
    "handle_validation_error",
    "load_cases",
    "load_raw_packets",
    "process_batch",
    "process_packet",
]

LOGGER = logging.getLogger("tvps.service")

#: Directory holding the deterministic demonstration data.
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"


def process_packet(
    raw_json: str | bytes | bytearray | None,
    processor: TelemetryProcessor | None = None,
) -> Result:
    """Run the full pipeline (parse -> validate -> process) on one packet.

    Args:
        raw_json: Raw JSON payload.
        processor: Optional processor holding the sequence history.  When it
            is omitted a fresh processor is used, which means the ordering
            check (REQ-005) has no history to compare against.

    Returns:
        A result envelope describing the outcome of the whole pipeline.
    """
    active = processor if processor is not None else TelemetryProcessor()
    try:
        parse_result = parse_telemetry(raw_json)
        if not parse_result["valid"]:
            return parse_result

        validation_result = validate_telemetry(parse_result["data"])
        if not validation_result["valid"]:
            return validation_result

        return active.process(validation_result["data"])
    except TVPSError as exc:
        LOGGER.error("telemetry processing failed: %s", exc)
        return result_from_error(exc)
    except Exception as exc:  # pragma: no cover - defensive, stays visible
        LOGGER.exception("unexpected error while processing a telemetry packet")
        return result_from_error(
            exc, extra_context={"traceback": traceback.format_exc()}
        )


def process_batch(
    packets: Sequence[str | bytes | bytearray | Mapping[str, Any] | None],
) -> Result:
    """Process a batch of telemetry packets.

    Each element of ``packets`` may be a raw JSON payload or an already
    decoded telemetry object.  The packets are processed in order and the
    sequence history is kept across the whole batch so that out-of-order
    packets are detected (REQ-005, REQ-009).

    Args:
        packets: The packets to process.

    Returns:
        A result envelope whose ``data`` holds the batch summary:
        ``total_packets``, ``valid_packets``, ``invalid_packets``,
        ``processed_packets``, per packet ``results`` and the
        ``error_details`` of every rejected packet.
    """
    processor = TelemetryProcessor()
    results: list[Result] = []
    for item in packets:
        results.append(_process_batch_item(item, processor))

    total = len(results)
    processed = sum(1 for r in results if r["status"] == STATUS_PROCESSED)
    valid = sum(1 for r in results if r["valid"])
    invalid = total - valid

    error_details: list[BatchErrorDetail] = []
    for index, result in enumerate(results):
        for detail in result["error_details"]:
            error_details.append(
                {
                    "code": detail["code"],
                    "field": detail["field"],
                    "message": detail["message"],
                    "context": detail["context"],
                    "index": index,
                    "status": result["status"],
                }
            )

    summary = {
        "total_packets": total,
        "valid_packets": valid,
        "invalid_packets": invalid,
        "processed_packets": processed,
        "results": results,
        "error_details": error_details,
    }

    if invalid == 0:
        status = STATUS_PROCESSED
    elif processed > 0:
        status = STATUS_PARTIAL
    else:
        status = STATUS_REJECTED

    return make_result(
        status=status,
        data=summary,
        errors=[detail["message"] for detail in error_details],
        error_details=error_details,
    )


def handle_validation_error(error: Any) -> Result:
    """Convert an error into an observable, structured result.

    The function accepts a :class:`~tvps.app.errors.ValidationError`, any
    other TVPS error, an arbitrary exception or a plain message and returns
    a rejected result envelope.  Nothing is swallowed: the error type and
    message are always visible in the returned envelope.

    Args:
        error: The error to report.

    Returns:
        A result envelope with ``valid`` ``False`` and ``status``
        ``"REJECTED"``.

    Example:
        >>> handle_validation_error("battery must be between 0 and 100")["errors"]
        ['battery must be between 0 and 100']
    """
    if isinstance(error, ValidationError):
        return result_from_error(error)
    if isinstance(error, TVPSError):
        return result_from_error(error)
    if isinstance(error, BaseException):
        return result_from_error(
            error, extra_context={"traceback": traceback.format_exc()}
        )
    if isinstance(error, Mapping):
        detail = make_error_detail(
            str(error.get("code", "VALIDATION_ERROR")),
            str(error.get("message", "unknown validation error")),
            field=error.get("field"),
            context=dict(error.get("context", {}) or {}),
        )
        return make_result(
            status=STATUS_REJECTED, errors=[detail["message"]], error_details=[detail]
        )
    return make_result(
        status=STATUS_REJECTED,
        errors=[str(error)],
        error_details=[
            make_error_detail("VALIDATION_ERROR", str(error))
        ],
    )


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load deterministic test cases from a JSON data file.

    The expected file format is a list of objects::

        [{"case": "<name>", "packet": {...}, "expected_error": "<message>"}]

    ``expected_error`` is optional and may be ``None`` for valid packets.

    Args:
        path: Path of the JSON file.

    Returns:
        The list of cases in file order.

    Raises:
        OSError: If the file cannot be read.
        json.JSONDecodeError: If the file does not contain valid JSON.
        ValueError: If the file content has an unexpected structure.
    """
    content = Path(path).read_text(encoding="utf-8")
    payload = json.loads(content)
    if not isinstance(payload, list):
        raise ValueError(
            f"data file {path} must contain a list of cases, "
            f"got {type(payload).__name__}"
        )
    cases: list[dict[str, Any]] = []
    for entry in payload:
        if not isinstance(entry, Mapping):
            raise ValueError(
                f"data file {path} must contain objects, got {type(entry).__name__}"
            )
        if "packet" not in entry:
            raise ValueError(f"data file {path} contains a case without a packet")
        cases.append(dict(entry))
    return cases


def load_raw_packets(path: str | Path) -> list[str]:
    """Load raw (possibly malformed) packets from a text file.

    Every non-empty line that does not start with ``#`` is one raw payload.

    Args:
        path: Path of the text file.

    Returns:
        The raw payloads in file order.

    Raises:
        OSError: If the file cannot be read.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def _process_batch_item(
    item: str | bytes | bytearray | Mapping[str, Any] | None,
    processor: TelemetryProcessor,
) -> Result:
    """Run the pipeline for a single batch element."""
    if isinstance(item, Mapping):
        parsed: Mapping[str, Any] = item
    else:
        parse_result = parse_telemetry(item)
        if not parse_result["valid"]:
            return parse_result
        parsed = parse_result["data"]

    validation_result = validate_telemetry(parsed)
    if not validation_result["valid"]:
        return validation_result

    return processor.process(validation_result["data"])
