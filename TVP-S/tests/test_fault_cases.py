"""Fault injection tests for TVPS.

The fault scenarios are supplied through the public API only - the
production code is never modified to create an error condition.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tvps import (
    STATUS_OUT_OF_ORDER,
    STATUS_REJECTED,
    TelemetryProcessor,
    process_batch,
    process_packet,
    process_telemetry,
    validate_telemetry,
)

FAULT_INPUTS = [
    pytest.param(None, id="none_input"),
    pytest.param("", id="empty_input"),
    pytest.param("   ", id="whitespace_input"),
    pytest.param("{", id="truncated_json"),
    pytest.param('{"sequence": }', id="invalid_value_json"),
    pytest.param("[1, 2, 3]", id="json_array"),
    pytest.param("garbage", id="garbage_text"),
    pytest.param(42, id="wrong_input_type"),
]


@pytest.mark.parametrize("payload", FAULT_INPUTS)
def test_fault_inputs_are_rejected_without_raising(payload: Any) -> None:
    result = process_packet(payload)

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert result["errors"], "a fault input must produce a visible error"
    assert result["data"] is None


@pytest.mark.parametrize("payload", FAULT_INPUTS)
def test_fault_inputs_are_rejected_by_the_parser(payload: Any) -> None:
    from tvps import parse_telemetry

    result = parse_telemetry(payload)

    assert result["valid"] is False
    assert result["error_details"][0]["code"] in {"PARSE_ERROR", "EMPTY_INPUT"}


def test_fault_missing_field_is_reported_with_its_field_name(base_packet: dict[str, Any]) -> None:
    del base_packet["battery"]

    result = process_packet(json.dumps(base_packet))

    assert result["errors"] == ["battery field is required"]
    assert result["error_details"][0]["field"] == "battery"
    assert result["error_details"][0]["code"] == "MISSING_FIELD"


def test_fault_invalid_type_is_reported_with_the_actual_type(base_packet: dict[str, Any]) -> None:
    base_packet["battery"] = "full"

    result = process_packet(json.dumps(base_packet))

    assert result["errors"] == ["battery must be a number"]
    assert result["error_details"][0]["context"]["actual_type"] == "str"
    assert result["error_details"][0]["context"]["expected_type"] == "a number"


def test_fault_invalid_range_is_reported_with_the_limits(base_packet: dict[str, Any]) -> None:
    base_packet["latitude"] = 120

    result = process_packet(json.dumps(base_packet))

    assert result["errors"] == ["latitude must be between -90 and 90"]
    assert result["error_details"][0]["context"]["minimum"] == -90
    assert result["error_details"][0]["context"]["maximum"] == 90


def test_fault_out_of_order_sequence_is_detected(base_packet: dict[str, Any]) -> None:
    processor = TelemetryProcessor()
    newer = dict(base_packet, sequence=42)
    older = dict(base_packet, sequence=7)

    assert processor.process(newer)["valid"] is True
    result = processor.process(older)

    assert result["valid"] is False
    assert result["status"] == STATUS_OUT_OF_ORDER
    assert result["errors"] == ["sequence 7 is out of order, expected greater than 42"]


def test_fault_out_of_order_sequence_is_detected_in_a_batch(base_packet: dict[str, Any]) -> None:
    packets = [
        dict(base_packet, sequence=42),
        dict(base_packet, sequence=7),
        dict(base_packet, sequence=43),
    ]

    result = process_batch(packets)
    summary = result["data"]

    assert summary["total_packets"] == 3
    assert summary["processed_packets"] == 2
    assert summary["invalid_packets"] == 1
    assert summary["error_details"][0]["code"] == "SEQUENCE_ORDER_ERROR"
    assert summary["error_details"][0]["index"] == 1


def test_every_data_file_fault_case_is_rejected(invalid_cases: list[dict[str, Any]]) -> None:
    assert invalid_cases

    for case in invalid_cases:
        result = process_packet(json.dumps(case["packet"]))
        assert result["valid"] is False, case["case"]
        assert case["expected_error"] in result["errors"], case["case"]
        assert result["error_details"], case["case"]


def test_every_malformed_data_file_packet_is_rejected(malformed_packets: list[str]) -> None:
    assert malformed_packets

    for raw in malformed_packets:
        result = process_packet(raw)
        assert result["valid"] is False, raw
        assert result["error_details"][0]["code"] == "PARSE_ERROR", raw


def test_faults_do_not_leak_exceptions_in_the_batch(invalid_cases: list[dict[str, Any]],
                                                    malformed_packets: list[str]) -> None:
    packets = [None, "", "{", json.dumps(invalid_cases[0]["packet"]), *malformed_packets]

    result = process_batch(packets)

    assert result["valid"] is False
    assert result["data"]["total_packets"] == len(packets)
    assert result["data"]["processed_packets"] == 0
    assert result["data"]["invalid_packets"] == len(packets)


def test_processing_never_returns_a_partial_result(base_packet: dict[str, Any]) -> None:
    del base_packet["sequence"]

    result = process_telemetry(base_packet)

    assert result["data"] is None
    assert result["valid"] is False


def test_validation_errors_are_reproducible(base_packet: dict[str, Any]) -> None:
    base_packet["battery"] = 250

    first = validate_telemetry(base_packet)
    second = validate_telemetry(base_packet)

    assert first == second
    assert first["error_details"] == second["error_details"]
