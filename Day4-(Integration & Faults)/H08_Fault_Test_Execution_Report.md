# H08 — Fault Test Execution Report

**Project:** RudraEdge T1 Testing (TVPS)
**Date:** 25 October 2026
**Activity:** Integration & Faults

## 1. Objective

Execute controlled software fault tests using synthetic inputs and record system handling of invalid inputs.

## 2. Fault Test Scope

- Missing mandatory field
- Invalid data type
- Malformed JSON input
- Out-of-range value
- Invalid sequence

No real UAV, hardware, flight environment, or external network was used.

## 3. Execution Results

| Test ID | Fault Scenario | Expected Handling | Observed Result | Status |
|---|---|---|---|---|
| FT-001 | Missing mandatory field | `MISSING_FIELDS:battery` | `MISSING_FIELDS:battery` | **PASS** |
| FT-002 | Invalid data type | `INVALID_TYPE:sequence` | `INVALID_TYPE:sequence` | **PASS** |
| FT-003 | Malformed JSON | `JSONDecodeError` | `JSONDecodeError` | **PASS** |
| FT-004 | Out-of-range battery | `OUT_OF_RANGE:battery` | `OUT_OF_RANGE:battery` | **PASS** |
| FT-005 | Invalid sequence | `INVALID_SEQUENCE` | `INVALID_SEQUENCE` | **PASS** |

**Execution Summary:** 5 fault tests executed — 5 PASS, 0 FAIL.

## 4. Handling Assessment

Each controlled fault was checked for rejection and an observable error condition before normal processing.

## 5. Conclusion

All 5 controlled fault cases produced the expected handling behavior.

## 6. Limitations

- Synthetic software inputs only.
- No hardware or real flight testing.
- Scope limited to the listed fault cases.