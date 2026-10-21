"""Unit tests for the TVPS validator (REQ-002, REQ-003, REQ-004, REQ-005)."""

from __future__ import annotations

from typing import Any

import pytest

from tvps import (
    MANDATORY_FIELDS,
    STATUS_REJECTED,
    STATUS_VALIDATED,
    ValidationError,
    collect_validation_errors,
    validate_or_raise,
    validate_telemetry,
)

# (field, value, is_valid) - the full boundary matrix of the requirement set.
BOUNDARY_MATRIX = [
    ("latitude", -90, True),
    ("latitude", 90, True),
    ("latitude", -91, False),
    ("latitude", 91, False),
    ("longitude", -180, True),
    ("longitude", 180, True),
    ("longitude", -181, False),
    ("longitude", 181, False),
    ("altitude", 0, True),
    ("altitude", 10000, True),
    ("altitude", -1, False),
    ("altitude", 10001, False),
    ("speed", 0, True),
    ("speed", 500, True),
    ("speed", -1, False),
    ("speed", 501, False),
    ("battery", 0, True),
    ("battery", 100, True),
    ("battery", -1, False),
    ("battery", 101, False),
    ("satellites", 0, True),
    ("satellites", 40, True),
    ("satellites", -1, False),
    ("satellites", 41, False),
]

TYPE_MATRIX = [
    ("sequence", "one", "sequence must be an integer"),
    ("sequence", 1.5, "sequence must be an integer"),
    ("sequence", True, "sequence must be an integer"),
    ("latitude", "12.5", "latitude must be a number"),
    ("longitude", "45.25", "longitude must be a number"),
    ("altitude", "120.5", "altitude must be a number"),
    ("speed", None, "speed must be a number"),
    ("battery", "full", "battery must be a number"),
    ("satellites", "twelve", "satellites must be an integer"),
    ("satellites", 12.5, "satellites must be an integer"),
    ("timestamp", 20240501, "timestamp must be a non-empty string"),
]

RANGE_MESSAGES = {
    "latitude": "latitude must be between -90 and 90",
    "longitude": "longitude must be between -180 and 180",
    "altitude": "altitude must be between 0 and 10000",
    "speed": "speed must be between 0 and 500",
    "battery": "battery must be between 0 and 100",
    "satellites": "satellites must be between 0 and 40",
}


def test_valid_packet_is_accepted() -> None:
    packet = {
        "timestamp": "2024-05-01T09:00:00Z",
        "sequence": 1,
        "latitude": 12.5,
        "longitude": 45.25,
        "altitude": 120.5,
        "speed": 33.0,
        "battery": 87.5,
        "satellites": 12,
    }

    result = validate_telemetry(packet)

    assert result["valid"] is True
    assert result["status"] == STATUS_VALIDATED
    assert result["errors"] == []
    assert result["error_details"] == []
    assert result["data"] == packet


@pytest.mark.parametrize("field", MANDATORY_FIELDS)
def test_missing_mandatory_field_is_rejected(base_packet: dict[str, Any], field: str) -> None:
    del base_packet[field]

    result = validate_telemetry(base_packet)

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert f"{field} field is required" in result["errors"]
    assert result["error_details"][0]["code"] == "MISSING_FIELD"
    assert result["error_details"][0]["field"] == field


def test_all_missing_fields_are_reported(base_packet: dict[str, Any]) -> None:
    result = validate_telemetry({})

    assert result["valid"] is False
    assert len(result["errors"]) == len(MANDATORY_FIELDS)
    for field in MANDATORY_FIELDS:
        assert f"{field} field is required" in result["errors"]


@pytest.mark.parametrize("field, value, message", TYPE_MATRIX)
def test_wrong_data_type_is_rejected(
    base_packet: dict[str, Any], field: str, value: Any, message: str
) -> None:
    base_packet[field] = value

    result = validate_telemetry(base_packet)

    assert result["valid"] is False
    assert message in result["errors"]
    assert result["error_details"][0]["code"] == "INVALID_TYPE"
    assert result["error_details"][0]["field"] == field


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_timestamp_is_rejected(base_packet: dict[str, Any], value: str) -> None:
    base_packet["timestamp"] = value

    result = validate_telemetry(base_packet)

    assert result["valid"] is False
    assert "timestamp must be a non-empty string" in result["errors"]
    assert result["error_details"][0]["code"] == "INVALID_VALUE"


@pytest.mark.parametrize("field, value, is_valid", BOUNDARY_MATRIX)
def test_range_boundaries_are_enforced(
    base_packet: dict[str, Any], field: str, value: Any, is_valid: bool
) -> None:
    base_packet[field] = value

    result = validate_telemetry(base_packet)

    assert result["valid"] is is_valid
    if is_valid:
        assert result["errors"] == []
    else:
        assert RANGE_MESSAGES[field] in result["errors"]
        assert result["error_details"][0]["code"] == "OUT_OF_RANGE"


@pytest.mark.parametrize("sequence", [0, -1, -100])
def test_non_positive_sequence_is_rejected(base_packet: dict[str, Any], sequence: int) -> None:
    base_packet["sequence"] = sequence

    result = validate_telemetry(base_packet)

    assert result["valid"] is False
    assert "sequence must be a positive integer" in result["errors"]


@pytest.mark.parametrize("sequence", [1, 2, 999999])
def test_positive_sequence_is_accepted(base_packet: dict[str, Any], sequence: int) -> None:
    base_packet["sequence"] = sequence

    result = validate_telemetry(base_packet)

    assert result["valid"] is True


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(base_packet: dict[str, Any], value: float) -> None:
    base_packet["latitude"] = value

    result = validate_telemetry(base_packet)

    assert result["valid"] is False
    assert RANGE_MESSAGES["latitude"] in result["errors"]


@pytest.mark.parametrize("payload", [None, "a string", 42, [1, 2, 3], (1, 2)])
def test_non_object_payload_is_rejected(payload: Any) -> None:
    result = validate_telemetry(payload)

    assert result["valid"] is False
    assert result["errors"] == [
        f"telemetry data must be a JSON object, got {type(payload).__name__}"
    ]
    assert result["error_details"][0]["code"] == "INVALID_PAYLOAD"


def test_multiple_errors_are_reported_together(base_packet: dict[str, Any]) -> None:
    del base_packet["battery"]
    base_packet["latitude"] = 91
    base_packet["sequence"] = "one"

    result = validate_telemetry(base_packet)

    assert result["valid"] is False
    assert result["errors"] == [
        "sequence must be an integer",
        "latitude must be between -90 and 90",
        "battery field is required",
    ]


def test_error_order_is_deterministic(base_packet: dict[str, Any]) -> None:
    del base_packet["battery"]
    base_packet["latitude"] = 91

    first = validate_telemetry(base_packet)
    second = validate_telemetry(base_packet)

    assert first == second
    assert first["errors"] == second["errors"]


def test_collect_validation_errors_returns_structured_details(base_packet: dict[str, Any]) -> None:
    del base_packet["satellites"]

    details = collect_validation_errors(base_packet)

    assert len(details) == 1
    assert details[0] == {
        "code": "MISSING_FIELD",
        "field": "satellites",
        "message": "satellites field is required",
        "context": {"mandatory_field": "satellites"},
    }


def test_validate_or_raise_returns_the_packet(base_packet: dict[str, Any]) -> None:
    assert validate_or_raise(base_packet) == base_packet


def test_validate_or_raise_raises_on_invalid_packet(base_packet: dict[str, Any]) -> None:
    del base_packet["battery"]

    with pytest.raises(ValidationError) as excinfo:
        validate_or_raise(base_packet)

    assert excinfo.value.message == "battery field is required"
    assert excinfo.value.details[0]["field"] == "battery"


def test_validation_does_not_mutate_the_input(base_packet: dict[str, Any]) -> None:
    snapshot = dict(base_packet)

    validate_telemetry(base_packet)

    assert base_packet == snapshot


def test_valid_data_file_cases_are_accepted(valid_cases: list[dict[str, Any]]) -> None:
    assert valid_cases

    for case in valid_cases:
        result = validate_telemetry(case["packet"])
        assert result["valid"] is True, f"case {case['case']} should be valid"


def test_invalid_data_file_cases_are_rejected(invalid_cases: list[dict[str, Any]]) -> None:
    assert invalid_cases

    for case in invalid_cases:
        result = validate_telemetry(case["packet"])
        assert result["valid"] is False, f"case {case['case']} should be invalid"
        assert case["expected_error"] in result["errors"]
