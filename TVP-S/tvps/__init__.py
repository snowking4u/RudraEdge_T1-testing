"""Telemetry Validation & Processing System (TVPS).

TVPS is a small, fully local software system that receives synthetic
telemetry packets, parses them, validates them, processes the valid ones
and reports every error it encounters.  It is used as a System Under Test
for systems test and verification activities.

The public API is available both from this package and from the
individual modules:

    >>> from tvps import parse_telemetry, validate_telemetry, process_telemetry
"""

from __future__ import annotations

from .app import (
    DATA_DIR,
    FIELD_SPECS,
    MANDATORY_FIELDS,
    STATUS_OUT_OF_ORDER,
    STATUS_PARSED,
    STATUS_PARTIAL,
    STATUS_PROCESSED,
    STATUS_REJECTED,
    STATUS_VALIDATED,
    BatchErrorDetail,
    ErrorDetail,
    ProcessingError,
    Result,
    SequenceOrderError,
    TelemetryParseError,
    TelemetryProcessor,
    TVPSError,
    ValidationError,
    collect_validation_errors,
    handle_validation_error,
    load_cases,
    load_raw_packets,
    normalise_telemetry,
    parse_telemetry,
    process_batch,
    process_packet,
    process_telemetry,
    validate_or_raise,
    validate_telemetry,
)

__version__ = "1.0.0"

__all__ = [
    "DATA_DIR",
    "BatchErrorDetail",
    "ErrorDetail",
    "FIELD_SPECS",
    "MANDATORY_FIELDS",
    "ProcessingError",
    "Result",
    "STATUS_OUT_OF_ORDER",
    "STATUS_PARSED",
    "STATUS_PARTIAL",
    "STATUS_PROCESSED",
    "STATUS_REJECTED",
    "STATUS_VALIDATED",
    "SequenceOrderError",
    "TVPSError",
    "TelemetryParseError",
    "TelemetryProcessor",
    "ValidationError",
    "__version__",
    "collect_validation_errors",
    "handle_validation_error",
    "load_cases",
    "load_raw_packets",
    "normalise_telemetry",
    "parse_telemetry",
    "process_batch",
    "process_packet",
    "process_telemetry",
    "validate_or_raise",
    "validate_telemetry",
]
