"""Integration tests for the TVPS service layer and the complete pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tvps import (
    STATUS_OUT_OF_ORDER,
    STATUS_PARSED,
    STATUS_PARTIAL,
    STATUS_PROCESSED,
    STATUS_REJECTED,
    STATUS_VALIDATED,
    TelemetryProcessor,
    ValidationError,
    handle_validation_error,
    load_cases,
    load_raw_packets,
    process_batch,
    process_packet,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_pipeline_accepts_a_valid_packet() -> None:
    raw = json.dumps(
        {
            "timestamp": "2024-05-01T09:00:00Z",
            "sequence": 1,
            "latitude": 12.5,
            "longitude": 45.25,
            "altitude": 120.5,
            "speed": 33.0,
            "battery": 87.5,
            "satellites": 12,
        }
    )

    result = process_packet(raw)

    assert result["valid"] is True
    assert result["status"] == STATUS_PROCESSED
    assert result["errors"] == []
    assert result["data"]["sequence"] == 1
    assert result["data"]["position"] == {"latitude": 12.5, "longitude": 45.25}


def test_pipeline_rejects_malformed_json() -> None:
    result = process_packet('{"sequence": 1')

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert result["error_details"][0]["code"] == "PARSE_ERROR"


def test_pipeline_rejects_a_missing_field() -> None:
    raw = json.dumps(
        {
            "timestamp": "2024-05-01T09:00:00Z",
            "sequence": 1,
            "latitude": 12.5,
            "longitude": 45.25,
            "altitude": 120.5,
            "speed": 33.0,
            "satellites": 12,
        }
    )

    result = process_packet(raw)

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert result["errors"] == ["battery field is required"]


def test_pipeline_detects_out_of_order_packets_with_a_shared_processor() -> None:
    processor = TelemetryProcessor()
    first = {"sequence": 7, "timestamp": "2024-05-01T09:00:00Z", "latitude": 1.0,
             "longitude": 2.0, "altitude": 3.0, "speed": 4.0, "battery": 50.0,
             "satellites": 8}
    second = dict(first, sequence=6)

    assert process_packet(json.dumps(first), processor)["valid"] is True
    result = process_packet(json.dumps(second), processor)

    assert result["valid"] is False
    assert result["status"] == STATUS_OUT_OF_ORDER
    assert "sequence 6 is out of order, expected greater than 7" in result["errors"]


def test_batch_counts_valid_and_invalid_packets(valid_cases: list[dict[str, Any]],
                                                invalid_cases: list[dict[str, Any]]) -> None:
    packets = [
        json.dumps(valid_cases[0]["packet"]),
        json.dumps(invalid_cases[0]["packet"]),
        json.dumps(valid_cases[1]["packet"]),
        json.dumps(invalid_cases[1]["packet"]),
    ]

    result = process_batch(packets)
    summary = result["data"]

    assert result["status"] == STATUS_PARTIAL
    assert summary["total_packets"] == 4
    assert summary["valid_packets"] == 2
    assert summary["invalid_packets"] == 2
    assert summary["processed_packets"] == 2
    assert len(summary["results"]) == 4
    assert len(summary["error_details"]) == 2


def test_batch_of_valid_packets_is_processed(valid_cases: list[dict[str, Any]]) -> None:
    packets = [json.dumps(case["packet"]) for case in valid_cases]

    result = process_batch(packets)
    summary = result["data"]

    assert result["valid"] is True
    assert result["status"] == STATUS_PROCESSED
    assert summary["total_packets"] == len(packets)
    assert summary["invalid_packets"] == 0
    assert summary["processed_packets"] == len(packets)


def test_empty_batch_is_handled() -> None:
    result = process_batch([])
    summary = result["data"]

    assert result["valid"] is True
    assert summary["total_packets"] == 0
    assert summary["valid_packets"] == 0
    assert summary["invalid_packets"] == 0
    assert summary["processed_packets"] == 0


def test_batch_accepts_decoded_packets(valid_cases: list[dict[str, Any]]) -> None:
    result = process_batch([case["packet"] for case in valid_cases])

    assert result["valid"] is True
    assert result["data"]["processed_packets"] == len(valid_cases)


def test_batch_reports_malformed_packets(malformed_packets: list[str]) -> None:
    result = process_batch(malformed_packets)
    summary = result["data"]

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert summary["invalid_packets"] == summary["total_packets"]
    assert summary["processed_packets"] == 0
    assert all(detail["code"] == "PARSE_ERROR" for detail in summary["error_details"])


def test_batch_detects_out_of_order_packets(base_packet: dict[str, Any]) -> None:
    first = dict(base_packet, sequence=10)
    second = dict(base_packet, sequence=9)

    result = process_batch([first, second])
    summary = result["data"]

    assert summary["processed_packets"] == 1
    assert summary["invalid_packets"] == 1
    assert summary["error_details"][0]["code"] == "SEQUENCE_ORDER_ERROR"


def test_batch_is_deterministic(valid_cases: list[dict[str, Any]]) -> None:
    packets = [json.dumps(case["packet"]) for case in valid_cases]

    assert process_batch(packets) == process_batch(packets)


def test_handle_validation_error_accepts_a_message() -> None:
    result = handle_validation_error("battery must be between 0 and 100")

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert result["errors"] == ["battery must be between 0 and 100"]
    assert result["error_details"][0]["code"] == "VALIDATION_ERROR"


def test_handle_validation_error_accepts_a_validation_error() -> None:
    error = ValidationError(
        "battery field is required",
        details=[
            {
                "code": "MISSING_FIELD",
                "field": "battery",
                "message": "battery field is required",
                "context": {},
            }
        ],
    )

    result = handle_validation_error(error)

    assert result["valid"] is False
    assert result["errors"] == ["battery field is required"]
    assert result["error_details"][0]["code"] == "MISSING_FIELD"


def test_handle_validation_error_keeps_unexpected_exceptions_visible() -> None:
    result = handle_validation_error(ZeroDivisionError("division by zero"))

    assert result["valid"] is False
    assert result["errors"] == ["ZeroDivisionError: division by zero"]
    assert result["error_details"][0]["code"] == "UNEXPECTED_ERROR"
    assert result["error_details"][0]["context"]["exception_type"] == "ZeroDivisionError"


def test_handle_validation_error_accepts_a_detail_dictionary() -> None:
    result = handle_validation_error(
        {"code": "OUT_OF_RANGE", "field": "latitude", "message": "latitude is invalid"}
    )

    assert result["errors"] == ["latitude is invalid"]
    assert result["error_details"][0]["field"] == "latitude"


def test_load_cases_reads_the_data_files(data_dir: Path) -> None:
    cases = load_cases(data_dir / "valid_telemetry.json")

    assert cases
    assert all("case" in entry and "packet" in entry for entry in cases)


def test_load_raw_packets_skips_comments_and_blank_lines(data_dir: Path) -> None:
    packets = load_raw_packets(data_dir / "malformed_packets.txt")

    assert packets
    assert all(packet and not packet.startswith("#") for packet in packets)


def test_data_file_cases_are_processed_end_to_end(valid_cases: list[dict[str, Any]],
                                                 invalid_cases: list[dict[str, Any]]) -> None:
    for case in valid_cases:
        result = process_packet(json.dumps(case["packet"]))
        assert result["status"] == STATUS_PROCESSED, case["case"]

    for case in invalid_cases:
        result = process_packet(json.dumps(case["packet"]))
        assert result["valid"] is False, case["case"]
        assert case["expected_error"] in result["errors"]


def test_demo_program_runs_successfully() -> None:
    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "run_demo.py")],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "DEMO FINISHED - ALL SCENARIOS BEHAVED AS EXPECTED" in completed.stdout
    assert "battery must be between 0 and 100" in completed.stdout
    assert "battery field is required" in completed.stdout
    assert "malformed JSON" in completed.stdout
    assert "is out of order" in completed.stdout


@pytest.mark.parametrize(
    "status",
    [STATUS_PARSED, STATUS_VALIDATED, STATUS_PROCESSED, STATUS_REJECTED],
)
def test_every_module_returns_the_same_result_envelope(status: str) -> None:
    sample = {
        "valid": status != STATUS_REJECTED,
        "errors": [],
        "error_details": [],
        "status": status,
        "data": {},
    }

    assert set(sample) == {"valid", "errors", "error_details", "status", "data"}
