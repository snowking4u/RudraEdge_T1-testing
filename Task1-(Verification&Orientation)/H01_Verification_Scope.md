# H01 — Verification Scope

## 1. Document Information

| Field | Value |
|---|---|
| Project | RudraEdge T1 Testing |
| System Under Verification | Telemetry Validation & Processing System (TVPS) |
| Document | H01 — Verification Scope |
| Purpose | Initial software verification scope definition |
| Verification Environment | Local / Offline Python Environment |

---

## 2. Objective

The objective of this document is to define the verification scope of
the Telemetry Validation & Processing System (TVPS).

The scope identifies:

- Software functions that are subject to verification
- Requirements applicable to the system
- Verification methods used for each function
- Expected observable behaviour
- Verification boundaries and limitations

The purpose is to establish a clear baseline for subsequent unit,
integration, fault, regression, and final verification activities.

---

## 3. System Overview

TVPS is a local software system for receiving, parsing, validating,
processing, and reporting the results of synthetic telemetry packets.

The system does not communicate with external networks, cloud services,
or external APIs.

The primary processing flow is:

    Raw JSON Payload
          |
          v
    parse_telemetry()
          |
          v
    validate_telemetry()
          |
          v
    process_telemetry()
          |
          v
    Normalised Result

For multiple packets, the system additionally supports:

    Multiple Telemetry Packets
             |
             v
       process_batch()
             |
             v
    Batch Processing Summary
       |      |      |      |
       v      v      v      v
     Total  Valid  Invalid Errors


---

## 4. Software Components in Scope

The following TVPS components are included in the verification scope:

| Component | Purpose |
|---|---|
| Parser | Converts raw JSON payloads into telemetry data |
| Validator | Checks mandatory fields, data types, and value ranges |
| Processor | Normalises valid telemetry and checks sequence ordering |
| Service | Provides the complete processing pipeline, batch processing, and error handling |
| Models | Defines telemetry data structures, field specifications, result envelopes, and status information |
| Errors | Defines the TVPS error hierarchy |
| Demo Program | Demonstrates defined reference scenarios |

---

## 5. Testable Functions

The following functions and interfaces are directly testable through
the public API.

| Function / Component | Verification Scope |
|---|---|
| `parse_telemetry()` | JSON parsing, valid payload handling, malformed JSON rejection |
| `validate_telemetry()` | Mandatory fields, data types, ranges, sequence validity |
| `process_telemetry()` | Telemetry normalisation and sequence-order detection |
| `process_batch()` | Multiple packet processing, counters, and error details |
| `process_packet()` | End-to-end processing of an individual raw JSON packet |
| `handle_validation_error()` | Structured validation error handling |
| `TelemetryProcessor` | Sequence history and ordering behaviour |
| `collect_validation_errors()` | Collection and structuring of validation failures |
| `validate_or_raise()` | Validation failure behaviour |
| `normalise_telemetry()` | Normalised telemetry representation |
| `load_cases()` / `load_raw_packets()` | Loading predefined synthetic test inputs |

---

## 6. Requirements Within Verification Scope

The following requirements are included in the verification baseline:

| Requirement ID | Verification Scope |
|---|---|
| REQ-001 | Valid telemetry acceptance |
| REQ-002 | Mandatory field validation |
| REQ-003 | Data type validation |
| REQ-004 | Range and boundary validation |
| REQ-005 | Sequence and out-of-order detection |
| REQ-006 | Malformed JSON handling |
| REQ-007 | Normalised telemetry processing |
| REQ-008 | Observable structured error handling |
| REQ-009 | Batch processing |
| REQ-010 | Deterministic behaviour |
| REQ-011 | Local/offline operation |
| REQ-012 | Public API availability |
| REQ-013 | Complete regression test execution |
| REQ-014 | Demonstration program |
| REQ-015 | Reproducible failure information |

---

## 7. Verification Methods

The following verification methods are used:

| Method | Description |
|---|---|
| UT | Unit Test — verification of an individual function using deterministic input |
| IT | Integration Test — verification of the complete JSON-to-result processing pipeline |
| FT | Fault Test — deliberate injection of invalid or malformed input |
| RT | Regression Test — execution of the complete automated pytest suite |
| DEMO | Demonstration using `run_demo.py` |

These methods provide evidence that the defined software behaviour
satisfies the applicable requirements.

---

## 8. Functional Verification Areas

### 8.1 Input Parsing

Verification will determine whether:

- Valid JSON telemetry can be parsed.
- Malformed JSON is rejected.
- Truncated or corrupted JSON produces an observable parsing error.

### 8.2 Telemetry Validation

Verification will cover:

- Mandatory field presence
- Data type correctness
- Minimum and maximum boundaries
- Out-of-range values
- Positive sequence numbers

### 8.3 Sequence Processing

Verification will determine whether:

- Correctly ordered telemetry is accepted.
- Out-of-order telemetry is detected.
- The out-of-order condition is observable and not silently discarded.

### 8.4 Telemetry Processing

Verification will determine whether valid telemetry is converted into
the defined normalised result containing:

- Sequence
- Timestamp
- Position
- Altitude
- Speed
- Battery
- Satellites
- Processing status

### 8.5 Error Handling

Verification will determine whether expected failures are returned
through the defined structured result format and whether errors remain
observable.

The verification specifically checks that errors are not silently
swallowed through constructs such as:

    except:
        pass

### 8.6 Batch Processing

Verification will cover:

- Multiple packet processing
- Total packet count
- Valid packet count
- Invalid packet count
- Processed packet count
- Error details

### 8.7 Determinism

Verification will confirm that identical input produces identical
results and that uncontrolled randomness is not used.

---

## 9. Non-Functional Verification Areas

The following non-functional characteristics are within scope:

### 9.1 Local Operation

The system shall operate without external network communication,
external APIs, or cloud services.

### 9.2 Reproducibility

Failures shall provide sufficient information to identify:

- Input condition
- Involved function
- Error type
- Error message

### 9.3 Regression Capability

The complete automated test suite shall be executable using:

    pytest -v

### 9.4 Public Testability

Core functions shall be directly importable and independently
testable.

---

## 10. Verification Boundaries

The following boundaries apply to this verification scope:

1. Verification is limited to the implemented TVPS software.
2. Verification uses synthetic telemetry data.
3. Verification is performed locally and offline.
4. Verification does not depend on external services or hardware.
5. Verification focuses on defined software behaviour and observable
   results.
6. Requirements outside the TVPS requirement baseline are not considered
   verified by this document.
7. No real UAV hardware, flight operation, navigation control, or
   physical sensor is part of this verification scope.

---

## 11. Known Limitations

The following limitations are acknowledged:

### Timestamp

The timestamp field is type-checked but is not independently parsed
or validated as a timestamp value.

### Sequence Ordering

Out-of-order detection requires sequence history. A single isolated
packet cannot independently establish whether it is out of order.

### Processing Model

The current system is in-memory and single-process.

### Thread Safety

`TelemetryProcessor` is not thread-safe.

### Unknown Fields

Unknown JSON members are ignored.

### Units

The implementation assumes the defined units for telemetry values,
including metres and kilometres per hour.

---

## 12. Verification Evidence

Verification evidence will be collected from:

- Pytest execution results
- Individual test results
- Fault-test results
- Integration-test results
- Regression-test results
- `run_demo.py` output
- Structured error output

Evidence shall be traceable to the applicable requirement and test case.

---

## 13. Scope Exit Criteria

The initial verification scope is considered established when:

- All applicable requirements are identified.
- Testable functions are identified.
- Verification methods are assigned.
- Verification boundaries are documented.
- Known limitations are documented.
- Requirements can be traced to verification activities.

Actual PASS/FAIL status will be assigned only after the corresponding
verification activity has been executed and evidence has been collected.

---

## 14. Traceability Baseline

The requirement baseline for this document is:

    REQ-001 through REQ-015

Detailed requirement-to-test mapping is maintained separately in:

    H02_Initial_Verification_Matrix.xlsx

The requirement definitions and their currently identified verification
methods are maintained in:

    docs/REQUIREMENTS.md
