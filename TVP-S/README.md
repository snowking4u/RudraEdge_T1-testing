# TVPS - Telemetry Validation & Processing System

TVPS is a small, fully local Python system that receives synthetic telemetry
packets, parses them, validates them, processes the valid ones and reports
every error it finds. It is used as a **System Under Test (SUT)** for systems
test and verification activities (scope analysis, unit testing, integration
testing, fault testing, regression testing, defect tracking and final
verification evidence).

---

## 1. Purpose

The system simulates a telemetry reception component:

```
Input JSON
    |
    v
  Parser      (json -> telemetry object, malformed input is reported)
    |
    v
  Validator   (mandatory fields, data types, ranges, sequence semantics)
    |
    v
  Processor   (normalised telemetry result, out-of-order detection)
    |
    v
  Result / Error  (structured, machine readable, never silently swallowed)
```

Every stage is a separate module with a small public surface, so each stage
can be exercised, mocked and verified in isolation.

## 2. System scope

**In scope**

* Parsing of JSON telemetry payloads (text or UTF-8 bytes).
* Validation of the eight mandatory telemetry fields.
* Range validation with accepted boundary values.
* Normalisation of valid telemetry into a result structure.
* Detection of out-of-order sequence numbers.
* Batch processing with a summary (total / valid / invalid / processed).
* Structured, reproducible error reporting.
* A demo program and a complete pytest suite.

**Out of scope**

* Real UAV control, navigation commands, weapon functionality or hardware IO.
* Any network, cloud or external API usage of any kind.
* Storage, persistence or transport of telemetry (in-memory only).
* Semantic interpretation of the timestamp (format is type-checked only).

The system processes **synthetic telemetry only**.

## 3. Architecture

```
<project root>/                <- run all commands from here
├── tvps/                      <- importable package
│   ├── __init__.py            <- public API re-exports
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py          <- field specs, result envelope, status codes
│   │   ├── errors.py          <- exception hierarchy (TVPSError, ...)
│   │   ├── parser.py          <- raw payload -> telemetry object
│   │   ├── validator.py       <- mandatory fields, types, ranges
│   │   ├── processor.py       <- normalisation + sequence ordering
│   │   └── service.py         <- pipeline orchestration, batch, error handling
│   └── data/                  <- deterministic demonstration data
│       ├── valid_telemetry.json
│       ├── invalid_telemetry.json
│       └── malformed_packets.txt
├── tests/                     <- pytest suite (166 tests)
│   ├── conftest.py
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_processor.py
│   ├── test_service.py
│   └── test_fault_cases.py
├── docs/
│   └── REQUIREMENTS.md        <- REQ-ID | Requirement | Verification Method
├── run_demo.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

Dependencies between the modules are strictly one-directional:

```
models  <-  errors  <-  parser
   ^                     ^
   |                     |
validator  <-  processor  <-  service
```

`models.py` and `errors.py` have no internal dependencies, which keeps them
free of import cycles and easy to test.

## 4. Requirements

The traceable requirement list (REQ-001 ... REQ-015) with the verification
method of every requirement is in [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).

| Area | Requirement |
| ---- | ----------- |
| REQ-001 | Valid telemetry is accepted and processed. |
| REQ-002 | Missing mandatory fields are rejected and named. |
| REQ-003 | Incorrect data types are rejected with a clear message. |
| REQ-004 | Ranges are enforced, boundary values are accepted. |
| REQ-005 | Sequence numbers are positive; out-of-order packets are identified. |
| REQ-006 | Malformed JSON is rejected with a JSON parsing error. |
| REQ-007 | Valid telemetry is processed into a normalised result. |
| REQ-008 | All errors are observable and returned as structured results. |
| REQ-009 | Batch processing reports totals, counts and error details. |
| REQ-010 | The behaviour is deterministic. |
| REQ-011 | The system is fully local (standard library only). |
| REQ-012 | The public functions are directly importable and testable. |
| REQ-013 | The complete suite runs with `pytest -v`. |
| REQ-014 | The demo program shows the eight reference scenarios. |
| REQ-015 | Failures are reproducible and identify the error type. |

## 5. Input format

A telemetry packet is a JSON **object** with eight mandatory fields:

```json
{
  "timestamp": "2024-05-01T09:00:00Z",
  "sequence": 1,
  "latitude": 12.5,
  "longitude": 45.25,
  "altitude": 120.5,
  "speed": 33.0,
  "battery": 87.5,
  "satellites": 12
}
```

The data files in `tvps/data/` use a case envelope so that the expected
outcome travels with the data:

```json
[
  {
    "case": "out_of_range_battery",
    "expected_error": "battery must be between 0 and 100",
    "packet": { "...": "..." }
  }
]
```

`malformed_packets.txt` contains one raw payload per line (lines starting
with `#` are comments); every line must be rejected by the parser.

## 6. Validation rules

| Field | Type | Accepted range | Error message (example) |
| ----- | ---- | -------------- | ----------------------- |
| `timestamp` | non-empty string | - | `timestamp must be a non-empty string` |
| `sequence` | integer | `> 0` | `sequence must be a positive integer` |
| `latitude` | number | -90 .. 90 | `latitude must be between -90 and 90` |
| `longitude` | number | -180 .. 180 | `longitude must be between -180 and 180` |
| `altitude` | number (metres) | 0 .. 10000 | `altitude must be between 0 and 10000` |
| `speed` | number (km/h) | 0 .. 500 | `speed must be between 0 and 500` |
| `battery` | number (percent) | 0 .. 100 | `battery must be between 0 and 100` |
| `satellites` | integer | 0 .. 40 | `satellites must be between 0 and 40` |

Additional rules:

* Boundary values are valid (`latitude = 90` is accepted, `latitude = 91` is
  rejected).
* Booleans are **not** accepted as numbers (`True` is not `1` for `battery`).
* `NaN` and `inf` are rejected - they are never inside a closed range.
* A missing field is reported as `<field> field is required`.
* All problems of a packet are reported together, in a deterministic order.

## 7. Result model and error handling

Every public function returns the **same envelope**:

```python
{
    "valid": False,
    "errors": ["battery must be between 0 and 100"],
    "error_details": [
        {
            "code": "OUT_OF_RANGE",
            "field": "battery",
            "message": "battery must be between 0 and 100",
            "context": {"value": 101, "minimum": 0, "maximum": 100},
        }
    ],
    "status": "REJECTED",
    "data": None,
}
```

| Key | Meaning |
| --- | ------- |
| `valid` | `True` only when the operation produced no error. |
| `errors` | Human readable messages (empty list when valid). |
| `error_details` | Structured counterpart of `errors` with code, field and context. |
| `status` | `PARSED`, `VALIDATED`, `PROCESSED`, `OUT_OF_ORDER`, `PARTIAL` or `REJECTED`. |
| `data` | The operation payload, `None` when the operation failed. |

Error codes:

| Code | Meaning |
| ---- | ------- |
| `EMPTY_INPUT` | `None` or blank input. |
| `PARSE_ERROR` | Malformed JSON or a JSON value that is not an object. |
| `INVALID_PAYLOAD` | The decoded payload is not an object. |
| `MISSING_FIELD` | A mandatory field is absent. |
| `INVALID_TYPE` | A field carries the wrong data type. |
| `INVALID_VALUE` | A field has the right type but an unusable value (empty timestamp). |
| `OUT_OF_RANGE` | A numeric value is outside the allowed range. |
| `SEQUENCE_ORDER_ERROR` | The packet arrived out of order. |
| `UNEXPECTED_ERROR` | An unexpected exception; type, message and traceback are kept. |

Error handling principles:

* There is **no** `except:` and **no** `except: pass` anywhere in the code.
* Expected input problems are converted into a rejected result - the reason is
  always visible in `errors` and `error_details`.
* Unexpected exceptions are converted into an `UNEXPECTED_ERROR` detail that
  keeps the exception type, message and traceback, and they are additionally
  logged through the `tvps.service` logger.
* `handle_validation_error(error)` turns any error (validation error, TVPS
  error, arbitrary exception or plain message) into the same envelope.

## 8. How to run the demo

```bash
# from the project root (the folder that contains tvps/, tests/ and run_demo.py)
python run_demo.py
```

The demo prints eight scenarios - valid telemetry, missing field, invalid
battery, invalid latitude, wrong data type, malformed JSON, out-of-order
sequence and batch processing - and exits with code `0` when every scenario
behaved as expected.

```
1. VALID TELEMETRY
Input      : {"timestamp":"2024-05-01T09:00:00Z","sequence":1,...}
Status     : PASS
Stage      : PROCESSING
Processing : PROCESSED
Data       : sequence=1 timestamp=2024-05-01T09:00:00Z position=(12.5, 45.25) ...
```

## 9. How to run the tests

```bash
# from the project root (the folder that contains tvps/, tests/ and run_demo.py)
python -m pytest -v        # or: pytest -v
```

No network access, no services and no fixtures outside the repository are
needed. The suite contains 166 tests (unit, integration, fault and regression
tests) and is split into five modules:

| Test module | Focus |
| ----------- | ----- |
| `tests/test_parser.py` | Valid payloads, malformed JSON, empty/None input, determinism |
| `tests/test_validator.py` | Mandatory fields, data types, the full boundary matrix, sequence rules |
| `tests/test_processor.py` | Normalised result, out-of-order detection, processor state |
| `tests/test_service.py` | Complete pipeline, batch processing, error handling, data files, demo run |
| `tests/test_fault_cases.py` | Fault injection through the public API only |

Single requirement examples:

```bash
pytest -v tests/test_validator.py::test_range_boundaries_are_enforced
pytest -v tests/test_fault_cases.py
```

## 10. Testable (public) functions

```python
from tvps import (
    parse_telemetry,        # raw JSON      -> Result(status="PARSED")
    validate_telemetry,     # telemetry     -> Result(status="VALIDATED")
    process_telemetry,      # telemetry     -> Result(status="PROCESSED")
    process_batch,          # list of packets -> Result(status="PROCESSED"/"PARTIAL")
    process_packet,         # one raw packet  -> Result (full pipeline)
    handle_validation_error,# error          -> Result(status="REJECTED")
    TelemetryProcessor,     # stateful processor (sequence history)
    load_cases,             # JSON data file  -> list of cases
    load_raw_packets,       # text data file -> list of raw payloads
)
```

Additional helpers: `collect_validation_errors`, `validate_or_raise`,
`normalise_telemetry`, `tvps.app.models.FIELD_SPECS`,
`tvps.app.models.MANDATORY_FIELDS`.

Signatures:

| Function | Signature | Returns |
| -------- | --------- | ------- |
| `parse_telemetry` | `(raw_json: str \| bytes \| bytearray \| None)` | `Result` |
| `validate_telemetry` | `(data: Mapping[str, Any])` | `Result` |
| `process_telemetry` | `(data: Mapping[str, Any], last_sequence: int \| None = None)` | `Result` |
| `process_packet` | `(raw_json, processor: TelemetryProcessor \| None = None)` | `Result` |
| `process_batch` | `(packets: Sequence[str \| bytes \| Mapping])` | `Result` with a batch summary in `data` |
| `handle_validation_error` | `(error: Any)` | `Result` |

Batch summary (`data` of `process_batch`):

| Key | Meaning |
| --- | ------- |
| `total_packets` | Number of packets in the batch. |
| `valid_packets` | Packets accepted without error. |
| `invalid_packets` | Packets rejected (parse, validation or ordering error). |
| `processed_packets` | Packets that produced a `PROCESSED` result. |
| `results` | The full result envelope of every packet, in input order. |
| `error_details` | One entry per failure, with the packet `index` and the `status`. |

## 11. Known limitations

* The `timestamp` is only type-checked (non-empty string); it is not parsed
  or checked against a calendar.
* Sequence ordering is enforced per processor instance and per batch. A
  single packet processed without history cannot be classified as
  out-of-order, because no previous sequence is known.
* Out-of-order packets are rejected (status `OUT_OF_ORDER`) and therefore
  counted as `invalid_packets`; they are not processed further.
* Telemetry is kept in memory only - there is no persistence, no queue and
  no transport.
* The system is single-process and not thread-safe: a `TelemetryProcessor`
  instance carries mutable sequence state.
* Additional JSON members (for example a `checksum`) are ignored by the
  validator and are not passed on to the normalised result.
* Units are assumed to be metres (altitude) and km/h (speed); no unit
  conversion is performed.

## 12. Environment

* Python 3.11 or newer (standard library only, no runtime dependency).
* `pytest >= 7.0` for the verification suite (see `requirements.txt`).
* `pyproject.toml` only configures pytest (`pythonpath`, `testpaths`); there
  is no build step and nothing has to be installed to run the system.
