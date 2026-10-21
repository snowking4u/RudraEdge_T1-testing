"""TVPS application package.

The package contains the four processing stages (parser, validator,
processor, service), the shared data model and the error hierarchy.  All
public functions are re-exported here for convenient direct import.
"""

from __future__ import annotations

from .errors import (
    ProcessingError,
    SequenceOrderError,
    TelemetryParseError,
    TVPSError,
    ValidationError,
)
from .models import (
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
    FieldKind,
    FieldSpec,
    Result,
)
from .parser import parse_telemetry
from .processor import TelemetryProcessor, normalise_telemetry, process_telemetry
from .service import (
    DATA_DIR,
    handle_validation_error,
    load_cases,
    load_raw_packets,
    process_batch,
    process_packet,
)
from .validator import (
    collect_validation_errors,
    validate_or_raise,
    validate_telemetry,
)

__all__ = [
    "DATA_DIR",
    "BatchErrorDetail",
    "ErrorDetail",
    "FIELD_SPECS",
    "FieldKind",
    "FieldSpec",
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
