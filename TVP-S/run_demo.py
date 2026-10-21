"""Demonstration program for the Telemetry Validation & Processing System.

Run it from the project root::

    python run_demo.py

The program walks through the eight scenarios that are relevant for the
verification activities (valid input, missing field, invalid value, invalid
type, malformed JSON, out-of-order sequence and batch processing) and prints
a readable, deterministic report.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from tvps import (
    DATA_DIR,
    STATUS_OUT_OF_ORDER,
    STATUS_PARSED,
    STATUS_PROCESSED,
    STATUS_REJECTED,
    STATUS_VALIDATED,
    Result,
    TelemetryProcessor,
    load_cases,
    load_raw_packets,
    process_batch,
    process_packet,
)

SEPARATOR = "=" * 78
SUB_SEPARATOR = "-" * 78

STAGE_BY_ERROR_CODE = {
    "EMPTY_INPUT": "PARSING",
    "PARSE_ERROR": "PARSING",
    "INVALID_PAYLOAD": "PARSING",
    "MISSING_FIELD": "VALIDATION",
    "INVALID_TYPE": "VALIDATION",
    "INVALID_VALUE": "VALIDATION",
    "OUT_OF_RANGE": "VALIDATION",
    "VALIDATION_ERROR": "VALIDATION",
    "SEQUENCE_ORDER_ERROR": "PROCESSING",
    "UNEXPECTED_ERROR": "PROCESSING",
}


def main() -> int:
    """Run every demo scenario and print the report.

    Returns:
        ``0`` when every scenario behaved as expected, ``1`` otherwise.
    """
    valid_cases = {case["case"]: case for case in load_cases(DATA_DIR / "valid_telemetry.json")}
    invalid_cases = {
        case["case"]: case for case in load_cases(DATA_DIR / "invalid_telemetry.json")
    }
    malformed_packets = load_raw_packets(DATA_DIR / "malformed_packets.txt")

    print(SEPARATOR)
    print("TVPS - TELEMETRY VALIDATION & PROCESSING SYSTEM - DEMO")
    print(SEPARATOR)

    failures = 0

    # 1 - valid telemetry -------------------------------------------------
    print()
    print("1. VALID TELEMETRY")
    print(SUB_SEPARATOR)
    result = _demo_case(valid_cases["baseline"])
    failures += _report("VALID TELEMETRY", result, expected_valid=True)

    # 2 - missing mandatory field ----------------------------------------
    print()
    print("2. MISSING MANDATORY FIELD")
    print(SUB_SEPARATOR)
    result = _demo_case(invalid_cases["missing_battery"])
    failures += _report(
        "MISSING BATTERY",
        result,
        expected_valid=False,
        expected_error="battery field is required",
    )

    # 3 - invalid battery -------------------------------------------------
    print()
    print("3. INVALID BATTERY")
    print(SUB_SEPARATOR)
    result = _demo_case(invalid_cases["out_of_range_battery"])
    failures += _report(
        "INVALID BATTERY",
        result,
        expected_valid=False,
        expected_error="battery must be between 0 and 100",
    )

    # 4 - invalid latitude ------------------------------------------------
    print()
    print("4. INVALID LATITUDE")
    print(SUB_SEPARATOR)
    result = _demo_case(invalid_cases["out_of_range_latitude"])
    failures += _report(
        "INVALID LATITUDE",
        result,
        expected_valid=False,
        expected_error="latitude must be between -90 and 90",
    )

    # 5 - wrong data type -------------------------------------------------
    print()
    print("5. WRONG DATA TYPE")
    print(SUB_SEPARATOR)
    result = _demo_case(invalid_cases["wrong_type_sequence"])
    failures += _report(
        "WRONG DATA TYPE",
        result,
        expected_valid=False,
        expected_error="sequence must be an integer",
    )

    # 6 - malformed JSON --------------------------------------------------
    print()
    print("6. MALFORMED JSON")
    print(SUB_SEPARATOR)
    print(f"Input      : {malformed_packets[0]}")
    result = process_packet(malformed_packets[0])
    failures += _report(
        "MALFORMED JSON",
        result,
        expected_valid=False,
        input_text=malformed_packets[0],
    )

    # 7 - out-of-order sequence ------------------------------------------
    print()
    print("7. OUT-OF-ORDER SEQUENCE")
    print(SUB_SEPARATOR)
    processor = TelemetryProcessor()
    first = processor.process(valid_cases["integer_values"]["packet"])
    second = processor.process(valid_cases["typical_flight"]["packet"])
    print(f"Input      : sequence {valid_cases['integer_values']['packet']['sequence']} (accepted)")
    print(f"Input      : sequence {valid_cases['typical_flight']['packet']['sequence']} (received afterwards)")
    print(f"Status     : {'PASS' if first['valid'] else 'REJECTED'}")
    print(f"Processing : {first['status']}")
    print(f"Status     : {'PASS' if second['valid'] else 'REJECTED'}")
    print(f"Processing : {second['status']}")
    for error in second["errors"]:
        print(f"Error      : {error}")
    if second["valid"]:
        failures += 1
        print("!! EXPECTED the out-of-order packet to be rejected")

    # 8 - batch processing ------------------------------------------------
    print()
    print("8. BATCH PROCESSING")
    print(SUB_SEPARATOR)
    batch = _demo_batch(valid_cases, invalid_cases, malformed_packets)
    failures += _report_batch(batch)

    print()
    print(SEPARATOR)
    if failures:
        print(f"DEMO FINISHED WITH {failures} UNEXPECTED RESULT(S)")
    else:
        print("DEMO FINISHED - ALL SCENARIOS BEHAVED AS EXPECTED")
    print(SEPARATOR)
    return 1 if failures else 0


def _demo_case(case: dict[str, Any]) -> Result:
    """Process a single data case and print its input description."""
    packet = case["packet"]
    raw = json.dumps(packet, separators=(",", ":"))
    print(f"Input      : {raw}")
    return process_packet(raw)


def _report(
    title: str,
    result: Result,
    *,
    expected_valid: bool,
    expected_error: str | None = None,
    input_text: str | None = None,
) -> int:
    """Print the outcome of a scenario and report unexpected behaviour."""
    print(f"Status     : {'PASS' if result['valid'] else 'REJECTED'}")
    print(f"Stage      : {_stage(result)}")
    print(f"Processing : {result['status']}")
    if result["errors"]:
        for error in result["errors"]:
            print(f"Error      : {error}")
    if result["data"]:
        print(f"Data       : {_describe(result['data'])}")

    problems = 0
    if result["valid"] != expected_valid:
        print(f"!! EXPECTED valid={expected_valid}")
        problems += 1
    if expected_error is not None and expected_error not in result["errors"]:
        print(f"!! EXPECTED error message '{expected_error}'")
        problems += 1
    if input_text is not None and result["valid"]:
        print("!! EXPECTED the malformed payload to be rejected")
        problems += 1
    return problems


def _report_batch(batch: Result) -> int:
    """Print the batch summary and report unexpected behaviour."""
    summary = batch["data"] or {}
    print(f"Status     : {'PASS' if batch['valid'] else 'REJECTED'}")
    print(f"Processing : {batch['status']}")
    print(f"Total      : {summary.get('total_packets')}")
    print(f"Valid      : {summary.get('valid_packets')}")
    print(f"Invalid    : {summary.get('invalid_packets')}")
    print(f"Processed  : {summary.get('processed_packets')}")
    print("Errors     :")
    for detail in summary.get("error_details", []):
        print(
            f"  - packet #{detail['index']} [{detail['code']}] {detail['message']}"
        )
    if not summary.get("total_packets"):
        print("!! EXPECTED a non-empty batch")
        return 1
    return 0


def _demo_batch(
    valid_cases: dict[str, Any],
    invalid_cases: dict[str, Any],
    malformed_packets: list[str],
) -> Result:
    """Build and process a mixed batch of valid and invalid packets."""
    packets = [
        json.dumps(valid_cases["baseline"]["packet"]),
        json.dumps(invalid_cases["missing_battery"]["packet"]),
        json.dumps(valid_cases["typical_flight"]["packet"]),
        malformed_packets[0],
        json.dumps(invalid_cases["out_of_range_battery"]["packet"]),
        json.dumps(valid_cases["integer_values"]["packet"]),
    ]
    print(f"Input      : {len(packets)} packets (valid and invalid packets mixed)")
    return process_batch(packets)


def _stage(result: Result) -> str:
    """Return the pipeline stage that produced the reported error."""
    for detail in result["error_details"]:
        stage = STAGE_BY_ERROR_CODE.get(detail["code"])
        if stage:
            return stage
    if result["status"] == STATUS_PARSED:
        return "PARSING"
    if result["status"] == STATUS_VALIDATED:
        return "VALIDATION"
    if result["status"] == STATUS_PROCESSED:
        return "PROCESSING"
    if result["status"] == STATUS_OUT_OF_ORDER:
        return "PROCESSING"
    return STATUS_REJECTED


def _describe(data: dict[str, Any]) -> str:
    """Return a short, human readable description of processed telemetry."""
    position = data.get("position") or {}
    return (
        f"sequence={data.get('sequence')} timestamp={data.get('timestamp')} "
        f"position=({position.get('latitude')}, {position.get('longitude')}) "
        f"altitude={data.get('altitude')} speed={data.get('speed')} "
        f"battery={data.get('battery')} satellites={data.get('satellites')}"
    )


if __name__ == "__main__":
    sys.exit(main())
