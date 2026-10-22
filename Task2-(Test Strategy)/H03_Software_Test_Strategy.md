# H03 — Software Test Strategy

## 1. Document Information

| Field | Value |
|---|---|
| Project | RudraEdge T1 Testing |
| System Under Verification | Telemetry Validation & Processing System (TVPS) |
| Document | H03 — Software Test Strategy |
| Purpose | Define the software testing and verification approach |
| Environment | Local / Offline Python Environment |
| Test Framework | Pytest |
| Test Data | Controlled synthetic telemetry |
| External Network | Not required |

## 2. Purpose and Objective

This document defines a structured and repeatable testing strategy for the Telemetry Validation & Processing System (TVPS).

The strategy defines:

- Applicable test levels
- Test-data categories
- Test-case design approach
- Positive, negative and boundary testing
- Pass/fail decision rules
- Evidence collection
- Requirements traceability
- Defect reporting
- Regression testing
- Test execution control
- Verification exit criteria

The objective is to verify that the implemented software satisfies its defined requirements and that failures are observable, reproducible and traceable.

---

## 3. System Under Verification

TVPS is a local software system for parsing, validating and processing synthetic telemetry.

The primary processing flow is:

```text
Raw Telemetry Input
        ↓
parse_telemetry()
        ↓
validate_telemetry()
        ↓
process_telemetry()
        ↓
Normalised Result
```

For multiple packets:

```text
Multiple Telemetry Packets
        ↓
process_batch()
        ↓
Summary + Individual Results
```

The system is verified as a software-only system using controlled synthetic inputs. No real UAV hardware, external cloud service or external telemetry source is required.

---

## 4. Verification Principles

### 4.1 Requirements-based testing

Every verification activity should be traceable to a defined requirement or verification objective.

### 4.2 Positive and negative testing

Testing shall include both valid inputs and deliberately invalid inputs.

### 4.3 Boundary-value testing

Values at, below and above defined limits shall be tested where applicable.

### 4.4 Observable failures

Failures should produce identifiable and useful error information. Errors must not be silently ignored.

### 4.5 Reproducibility

The same input and test conditions should produce consistent results.

### 4.6 Evidence-based verification

A requirement shall only be considered PASS when execution evidence demonstrates that the expected result was achieved.

### 4.7 Regression protection

Previously verified functionality shall be rechecked after relevant software changes.

### 4.8 Local/offline execution

Testing shall remain executable in the local environment without dependence on external network services.

---

## 5. Test Levels

### 5.1 Unit Testing (UT)

Unit testing verifies individual functions or small software units independently.

Typical areas include:

- Telemetry parsing
- Mandatory-field validation
- Data-type validation
- Range validation
- Sequence validation
- Normalisation
- Error handling
- Deterministic processing

**Objective:** Verify that individual functions produce the expected result for defined inputs.

### 5.2 Integration Testing (IT)

Integration testing verifies interaction between multiple TVPS components.

Example:

```text
Raw JSON
   ↓
Parser
   ↓
Validator
   ↓
Processor
   ↓
Service Result
```

Integration testing checks that:

- Parsed data is correctly passed to validation
- Validated data is correctly passed to processing
- Errors are propagated correctly
- Batch processing produces correct summaries
- Component interfaces remain compatible

**Objective:** Verify that connected components work correctly as a complete processing flow.

### 5.3 Fault Testing (FT)

Fault testing deliberately introduces invalid or unexpected conditions.

Examples include:

- Missing mandatory fields
- Wrong data types
- Out-of-range values
- Boundary violations
- Out-of-order sequence values
- Malformed JSON
- Truncated JSON
- Invalid structures
- Unexpected runtime errors

**Objective:** Verify that the system rejects invalid conditions correctly and produces observable error information.

### 5.4 Regression Testing (RT)

Regression testing verifies that previously working functionality remains correct after software changes.

Typical command:

```bash
python -m pytest -v
```

**Objective:** Detect unintended changes or breakage in previously verified functionality.

### 5.5 Demonstration Testing (DEMO)

Demonstration testing executes defined end-to-end scenarios using the project demonstration script.

Typical command:

```bash
python run_demo.py
```

**Objective:** Provide a reproducible end-to-end verification of observable system behavior.

---

## 6. Test Data Strategy

Testing shall use controlled synthetic telemetry data.

### 6.1 Valid telemetry

Used to verify normal acceptance and processing.

Expected behavior:

```text
Valid input → Accepted → Processed successfully
```

### 6.2 Missing mandatory fields

Used to verify mandatory-field validation.

Expected behavior:

```text
Missing field → Rejected → Field-specific error
```

### 6.3 Incorrect data types

Used to verify type validation.

Expected behavior:

```text
Wrong type → Rejected → Validation error
```

### 6.4 Boundary and out-of-range values

Values around defined limits shall be tested.

Generic pattern:

```text
Minimum - 1 → Invalid
Minimum     → Valid
Nominal     → Valid
Maximum     → Valid
Maximum + 1 → Invalid
```

Where applicable, invalid numerical values such as NaN and infinity shall also be tested.

### 6.5 Sequence conditions

Both ordered and out-of-order telemetry sequences shall be tested.

```text
Correct sequence    → Accepted
Out-of-order packet → Detected / Rejected
```

### 6.6 Malformed input

Examples include:

- Invalid JSON syntax
- Truncated JSON
- Invalid structure
- Missing required data

Expected behavior:

```text
Malformed input → Parse failure → Structured error
```

### 6.7 Batch data

Multiple telemetry packets shall be used to verify:

- Total packet count
- Valid packet count
- Invalid packet count
- Error count
- Individual packet results

---

## 7. Test Case Design Approach

Each standard test case should define:

1. Test Case ID
2. Requirement ID
3. Objective
4. Preconditions
5. Inputs / Test Data
6. Test Steps
7. Expected Result
8. Actual Result
9. Pass/Fail Criteria
10. Evidence
11. Status
12. Defect ID, if applicable
13. Remarks

The test case should be specific enough that another tester can reproduce the same test using the documented conditions.

---

## 8. Positive Testing

Positive testing verifies that valid inputs are accepted and processed correctly.

Example:

```text
Valid telemetry
      ↓
Parser accepts
      ↓
Validator accepts
      ↓
Processor generates normalized result
```

The test passes when actual behavior matches the defined expected behavior.

---

## 9. Negative Testing

Negative testing verifies safe and predictable rejection of invalid inputs.

Examples:

- Missing mandatory field
- Wrong data type
- Out-of-range value
- Malformed JSON
- Out-of-order sequence
- Invalid structure

A negative test is considered PASS when the system correctly detects and handles the invalid condition.

---

## 10. Boundary Testing

Boundary testing focuses on values close to accepted limits.

For a defined range:

```text
Minimum - 1 → Invalid
Minimum     → Valid
Nominal     → Valid
Maximum     → Valid
Maximum + 1 → Invalid
```

Boundary tests are important because incorrect handling at limits can result in invalid data being accepted or valid data being rejected.

Where applicable, special numerical values such as NaN and infinity shall also be tested.

---

## 11. Pass / Fail / Blocked / Not Tested Rules

### PASS

A test is marked **PASS** only when:

- The test was actually executed
- The expected result was defined
- The actual result satisfies the expected result
- Required evidence is available

### FAIL

A test is marked **FAIL** when:

- The test was executed
- The actual result does not satisfy the expected result

A failed test shall be associated with a defect or documented technical observation.

### BLOCKED

A test is marked **BLOCKED** when it cannot be executed because a required dependency, environment or prerequisite is unavailable.

A blocked test must not be treated as PASS.

### NOT TESTED

A test is marked **NOT TESTED** when execution has not yet occurred.

A test must not be marked PASS merely because the implementation appears correct.

---

## 12. Evidence Strategy

Evidence shall be collected in a form that allows the verification result to be independently reviewed.

Possible evidence includes:

- Pytest execution output
- Individual test results
- Demonstration output
- Structured result/error data
- Logs
- Relevant source/review results
- Screenshots where applicable

Evidence should demonstrate:

```text
What was tested
      ↓
What input was used
      ↓
What was expected
      ↓
What actually happened
      ↓
Why the result is PASS/FAIL
```

Evidence should be traceable to the associated test case and requirement wherever practical.

---

## 13. Requirements Traceability

The basic verification relationship is:

```text
Requirement
     ↓
Test Case
     ↓
Verification Method
     ↓
Expected Result
     ↓
Execution
     ↓
Evidence
     ↓
PASS / FAIL / BLOCKED / NOT TESTED
```

This ensures that requirements are not tested informally without a defined verification path.

---

## 14. Defect Reporting Strategy

When a test does not meet its expected result, a defect shall be recorded.

A defect record should contain:

| Field | Description |
|---|---|
| Defect ID | Unique identifier |
| Requirement ID | Related requirement |
| Test Case ID | Test that detected the issue |
| Condition | Input or test condition |
| Expected Result | Required behavior |
| Actual Result | Observed behavior |
| Severity/Priority | Impact classification |
| Reproduction | Steps/input required to reproduce |
| Status | Open / Fixed / Retest / Closed |
| Evidence | Supporting test output |

A defect should remain traceable to the test case that detected it.

---

## 15. Defect Lifecycle

The general defect flow is:

```text
Test Failure
    ↓
Defect Identified
    ↓
Defect Recorded
    ↓
Root Cause Analysis
    ↓
Fix Implemented
    ↓
Retest
    ↓
Regression Test
    ↓
Closed
```

A defect should only be considered closed after the corrective change has been verified.

---

## 16. Regression Strategy

Regression testing shall be used after relevant changes to:

- Parser logic
- Validation rules
- Processing logic
- Error handling
- Service behavior
- Public interfaces

Regression testing should confirm that:

1. Existing valid inputs still work.
2. Existing invalid inputs are still rejected.
3. Error behavior remains observable.
4. Existing interfaces remain usable.
5. Previously verified requirements remain satisfied.

---

## 17. Test Environment

The verification environment is:

```text
Operating Environment : Local development environment
Runtime               : Python
Test Framework        : Pytest
Data                  : Synthetic telemetry
Execution             : Local / Offline
External Cloud        : None
External Network      : None
```

Testing does not require external cloud services or public network access.

---

## 18. Test Execution Control

### Before execution

The tester should confirm:

- Correct software version is available
- Required test data is available
- Preconditions are satisfied
- Test case is clearly identified
- Expected result is known

### During execution

The tester should:

- Record the actual result
- Preserve relevant output
- Record failures accurately
- Avoid changing the expected result after seeing the actual result
- Never manually convert a failure into PASS

### After execution

The tester should:

- Assign the correct status
- Attach evidence
- Record defects where required
- Perform regression testing after fixes

---

## 19. Exit Criteria

For a defined verification scope, testing may be considered complete when:

- All applicable requirements have a verification method.
- Required test cases have been executed.
- Expected and actual results are recorded.
- Required evidence is available.
- No unresolved critical verification failure remains unexplained.
- Failed tests are resolved and re-tested or formally documented.
- Required regression testing is completed.
- Final verification status is recorded.

---

## 20. Verification Reporting

Final reporting should summarize:

- Requirements covered
- Test cases executed
- Number of PASS results
- Number of FAIL results
- Number of BLOCKED tests
- Number of NOT TESTED cases
- Identified defects
- Retest/regression results
- Supporting evidence

The final result shall be based on recorded execution evidence rather than assumptions.

---

## 21. Overall Verification Flow

```text
Requirements
     ↓
Test Strategy
     ↓
Test Case Design
     ↓
Test Data Preparation
     ↓
Test Execution
     ↓
Evidence Collection
     ↓
PASS / FAIL / BLOCKED / NOT TESTED
     ↓
Defect Reporting
     ↓
Retest & Regression
     ↓
Verification Report
```

---

## 22. Summary

The TVPS testing strategy follows a requirements-based, structured and evidence-driven approach.

It combines:

- Unit testing
- Integration testing
- Fault testing
- Regression testing
- Demonstration testing
- Positive testing
- Negative testing
- Boundary-value testing
- Requirements traceability
- Evidence-based pass/fail decisions
- Defect reporting and re-verification

The strategy provides a consistent method for verifying software functionality, handling invalid conditions, maintaining traceability and producing reproducible verification results.
