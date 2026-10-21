# H02 — Initial Verification Matrix

## 1. Document Information

| Field | Value |
|---|---|
| Project | RudraEdge T1 Testing |
| System Under Verification | Telemetry Validation & Processing System (TVPS) |
| Document | H02 — Initial Verification Matrix |
| Environment | Local / Offline Python Environment |
| Status | Initial Verification Baseline |

---

## 2. Verification Methods

| Method | Description |
|---|---|
| UT | Unit Test |
| IT | Integration Test |
| FT | Fault Test |
| RT | Regression Test |
| DEMO | Demonstration using run_demo.py |

---

## 3. Verification Matrix

| Req ID | Test Case | Method | Expected Result | Evidence | Status |
|---|---|---|---|---|---|
| REQ-001 | TC-001 Valid telemetry acceptance | UT / IT / DEMO | Valid telemetry packet is parsed, validated and accepted | pytest + demo | NOT TESTED |
| REQ-002 | TC-002 Missing mandatory field | UT / FT / DEMO | Packet is rejected and missing field is reported | pytest + demo | NOT TESTED |
| REQ-003 | TC-003 Invalid data type | UT / FT / DEMO | Wrong data type is rejected with clear error information | pytest + demo | NOT TESTED |
| REQ-004 | TC-004 Range and boundary validation | UT / FT / DEMO | Valid boundaries are accepted and out-of-range values are rejected | pytest + demo | NOT TESTED |
| REQ-005 | TC-005 Sequence validation | UT / FT / DEMO | Positive sequence accepted; out-of-order packet is detected and reported | pytest + demo | NOT TESTED |
| REQ-006 | TC-006 Malformed JSON | FT / DEMO | Malformed/truncated JSON is rejected with parsing error | pytest + demo | NOT TESTED |
| REQ-007 | TC-007 Normalised processing result | UT / IT | Valid telemetry produces the required normalized result | pytest | NOT TESTED |
| REQ-008 | TC-008 Structured error handling | FT | Errors are observable and are not silently swallowed | pytest | NOT TESTED |
| REQ-009 | TC-009 Batch processing | IT / DEMO | Batch counters and individual packet results are correct | pytest + demo | NOT TESTED |
| REQ-010 | TC-010 Deterministic processing | UT / IT | Same input produces the same result | pytest | NOT TESTED |
| REQ-011 | TC-011 Local/offline operation | RT / Review | System operates without network, cloud or external runtime dependency | pytest + source review | NOT TESTED |
| REQ-012 | TC-012 Public API verification | UT / RT | Required public functions can be imported and tested independently | pytest | NOT TESTED |
| REQ-013 | TC-013 Complete regression suite | RT | Complete pytest suite executes successfully | pytest -v | NOT TESTED |
| REQ-014 | TC-014 Demo verification | IT / DEMO | run_demo.py executes all reference scenarios successfully | demo output | NOT TESTED |
| REQ-015 | TC-015 Reproducible failure reporting | UT / FT | Failure identifies input condition, function, error type and message | pytest | NOT TESTED |

---

## 4. Verification Status Definitions

| Status | Meaning |
|---|---|
| PASS | Test executed and expected result achieved |
| FAIL | Test executed but expected result was not achieved |
| BLOCKED | Test could not execute because a required dependency/environment was unavailable |
| NOT TESTED | Test has not yet been executed |

Only executed tests shall be marked PASS.

---

## 5. Verification Baseline

The initial verification baseline contains:

- 15 traceable requirements
- 15 primary test cases
- Unit, Integration, Fault, Regression and Demonstration methods
- Expected result defined for every requirement
- Evidence source defined for every requirement

Detailed test function references are maintained in `docs/REQUIREMENTS.md`.

---

## 6. Verification Objective

The objective of H02 is to establish complete requirement-to-test coverage before execution.

The next verification activity shall execute the defined tests and update:

- Actual Result
- Evidence
- Status
- Defects, if any

No requirement shall be marked PASS without execution evidence.
