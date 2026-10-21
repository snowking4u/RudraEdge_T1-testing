# TVPS - Requirements and Verification Traceability

This document is the traceable requirement list of the Telemetry Validation
& Processing System (TVPS). Every requirement below is implemented by the
system and verified by an automated test or by the demo program.

Verification methods used in this document:

| Method | Description |
| ------ | ----------- |
| UT | Unit test (function level, deterministic input) |
| IT | Integration test (complete pipeline, JSON -> result) |
| FT | Fault test (deliberately invalid input, injected through the public API) |
| RT | Regression test (complete pytest suite) |
| DEMO | Demonstrated by `run_demo.py` |

## Requirement list

| REQ-ID | Requirement | Verification Method |
| ------ | ----------- | ------------------- |
| REQ-001 | The system shall accept a syntactically valid telemetry packet containing all mandatory fields and valid values (JSON parsed, validation passed, packet accepted for processing). | UT (`test_parser.py::test_valid_payload_is_parsed_into_a_telemetry_object`, `test_validator.py::test_valid_packet_is_accepted`), IT (`test_service.py::test_pipeline_accepts_a_valid_packet`), DEMO (scenario 1) |
| REQ-002 | The system shall reject telemetry packets when any mandatory field (`timestamp`, `sequence`, `latitude`, `longitude`, `altitude`, `speed`, `battery`, `satellites`) is missing, and shall report the missing field. | UT (`test_validator.py::test_missing_mandatory_field_is_rejected`, `::test_all_missing_fields_are_reported`), FT (`test_fault_cases.py::test_fault_missing_field_is_reported_with_its_field_name`), DEMO (scenario 2) |
| REQ-003 | The system shall reject telemetry packets that contain incorrect data types (e.g. `sequence` as string, `latitude` as string, `battery` as string, `satellites` as string) and shall return clear error information. | UT (`test_validator.py::test_wrong_data_type_is_rejected`), FT (`test_fault_cases.py::test_fault_invalid_type_is_reported_with_the_actual_type`), DEMO (scenario 5) |
| REQ-004 | The system shall validate telemetry values against the defined ranges (latitude -90..90, longitude -180..180, altitude 0..10000 m, speed 0..500 km/h, battery 0..100 %, satellites 0..40), accepting the boundary values and rejecting values outside the limits. | UT (`test_validator.py::test_range_boundaries_are_enforced` - full boundary matrix), FT (`test_fault_cases.py::test_fault_invalid_range_is_reported_with_the_limits`), DEMO (scenarios 3 and 4) |
| REQ-005 | Telemetry sequence numbers shall be positive integers. The processor shall identify out-of-order telemetry packets; correctly ordered packets are accepted, out-of-order packets generate an observable result and the condition is never silently discarded. | UT (`test_validator.py::test_non_positive_sequence_is_rejected`, `test_processor.py::test_out_of_order_packet_is_detected`, `::test_processor_detects_out_of_order_packets`), FT (`test_fault_cases.py::test_fault_out_of_order_sequence_is_detected`), DEMO (scenario 7) |
| REQ-006 | The system shall reject malformed JSON (missing closing brace, invalid quotation marks, corrupted structure, truncated JSON) with a clear JSON parsing error, without crashing unexpectedly. | UT (`test_parser.py::test_malformed_json_is_rejected_with_a_parse_error`), FT (`test_fault_cases.py::test_every_malformed_data_file_packet_is_rejected`), DEMO (scenario 6) |
| REQ-007 | Valid telemetry shall be processed into a normalised result containing `sequence`, `timestamp`, `position`, `altitude`, `speed`, `battery`, `satellites` and the processing status, represented as a plain dictionary. | UT (`test_processor.py::test_valid_packet_is_processed_into_a_normalised_result`, `::test_processed_result_contains_every_required_field`), IT (`test_service.py::test_pipeline_accepts_a_valid_packet`) |
| REQ-008 | All expected validation and parsing errors shall be observable and returned as structured results (`{"valid": ..., "errors": [...]}`). Unexpected exceptions shall remain visible; no error shall be swallowed with a bare `except:` or `except: pass`. | UT (`test_service.py::test_handle_validation_error_accepts_a_message`, `::test_handle_validation_error_keeps_unexpected_exceptions_visible`), FT (`test_fault_cases.py::test_fault_inputs_are_rejected_without_raising`) |
| REQ-009 | The system shall support batch processing of multiple telemetry packets and report total packets, valid packets, invalid packets, processed packets and error details. | UT (`test_service.py::test_batch_counts_valid_and_invalid_packets`, `::test_batch_of_valid_packets_is_processed`, `::test_empty_batch_is_handled`), IT (`test_service.py::test_batch_detects_out_of_order_packets`), DEMO (scenario 8) |
| REQ-010 | The system shall be deterministic: the same input always produces the same output and no uncontrolled randomness is used. | UT (`test_parser.py::test_parsing_is_deterministic`, `test_validator.py::test_error_order_is_deterministic`, `test_processor.py::test_processing_is_deterministic`), IT (`test_service.py::test_batch_is_deterministic`) |
| REQ-011 | The system shall be fully local: no internet access, no external APIs, no cloud services, no network communication of any kind, standard library only. | Review of `requirements.txt` (no runtime dependency), review of the source (no `socket`/`requests`/`urllib` import), RT (`pytest -v` runs offline) |
| REQ-012 | The system shall expose the public functions `parse_telemetry`, `validate_telemetry`, `process_telemetry`, `process_batch` and `handle_validation_error` for direct import and independent testing. | UT (every test module imports the functions directly), RT (`pytest -v`) |
| REQ-013 | The complete pytest suite shall be runnable with `pytest -v`, and a change in one module shall not require the manual execution of individual tests. | RT (`pytest -v` from the project root) |
| REQ-014 | The demo program `run_demo.py` shall demonstrate the eight reference scenarios (valid, missing field, invalid battery, invalid latitude, wrong type, malformed JSON, out-of-order sequence, batch) with readable output. | IT (`test_service.py::test_demo_program_runs_successfully`), DEMO |
| REQ-015 | Failures shall be reproducible: every failed operation shall identify the input condition, the involved function, the error type and the error message. | UT (`test_validator.py::test_collect_validation_errors_returns_structured_details`), FT (`test_fault_cases.py::test_validation_errors_are_reproducible`) |

## Notes

* The requirement list above contains only requirements that are implemented
  by this system; no requirement refers to functionality outside TVPS.
* The "verification method" column names the test functions that provide the
  evidence. Test names are stable and can be executed individually, e.g.
  `pytest -v tests/test_validator.py::test_range_boundaries_are_enforced`.
* REQ-001 to REQ-010 correspond one-to-one with the requirement set of the
  task definition; REQ-011 to REQ-015 describe the non-functional and
  deliverable constraints that are equally verifiable.
