"""Unit tests for the TVPS processor (REQ-005, REQ-007)."""

from __future__ import annotations

from typing import Any

import pytest

from tvps import (
    STATUS_OUT_OF_ORDER,
    STATUS_PROCESSED,
    STATUS_REJECTED,
    TelemetryProcessor,
    normalise_telemetry,
    process_telemetry,
)


def test_valid_packet_is_processed_into_a_normalised_result(base_packet: dict[str, Any]) -> None:
    result = process_telemetry(base_packet)

    assert result["valid"] is True
    assert result["status"] == STATUS_PROCESSED
    assert result["errors"] == []
    assert result["data"] == {
        "sequence": 1,
        "timestamp": "2024-05-01T09:00:00Z",
        "position": {"latitude": 12.5, "longitude": 45.25},
        "altitude": 120.5,
        "speed": 33.0,
        "battery": 87.5,
        "satellites": 12,
        "status": STATUS_PROCESSED,
    }


def test_processed_result_contains_every_required_field(base_packet: dict[str, Any]) -> None:
    result = process_telemetry(base_packet)

    assert result["data"] is not None
    for field in (
        "sequence",
        "timestamp",
        "position",
        "altitude",
        "speed",
        "battery",
        "satellites",
        "status",
    ):
        assert field in result["data"]


def test_position_is_normalised_into_a_nested_structure(base_packet: dict[str, Any]) -> None:
    result = process_telemetry(base_packet)

    assert result["data"]["position"] == {"latitude": 12.5, "longitude": 45.25}


def test_numeric_values_are_normalised_to_numbers(base_packet: dict[str, Any]) -> None:
    base_packet["latitude"] = 12
    base_packet["battery"] = 87

    result = process_telemetry(base_packet)

    assert result["data"]["position"]["latitude"] == 12.0
    assert isinstance(result["data"]["position"]["latitude"], float)
    assert result["data"]["battery"] == 87.0
    assert result["data"]["satellites"] == 12
    assert isinstance(result["data"]["satellites"], int)


def test_invalid_packet_is_rejected_without_raising(base_packet: dict[str, Any]) -> None:
    del base_packet["battery"]

    result = process_telemetry(base_packet)

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert result["data"] is None
    assert "battery field is required" in result["errors"]


def test_out_of_order_packet_is_detected(base_packet: dict[str, Any]) -> None:
    result = process_telemetry(base_packet, last_sequence=10)

    assert result["valid"] is False
    assert result["status"] == STATUS_OUT_OF_ORDER
    assert result["data"] is None
    assert result["errors"] == [
        "sequence 1 is out of order, expected greater than 10"
    ]
    assert result["error_details"][0]["code"] == "SEQUENCE_ORDER_ERROR"
    assert result["error_details"][0]["context"]["last_sequence"] == 10


def test_packet_with_newer_sequence_is_accepted(base_packet: dict[str, Any]) -> None:
    base_packet["sequence"] = 11

    result = process_telemetry(base_packet, last_sequence=10)

    assert result["valid"] is True
    assert result["status"] == STATUS_PROCESSED


def test_duplicate_sequence_is_detected(base_packet: dict[str, Any]) -> None:
    result = process_telemetry(base_packet, last_sequence=1)

    assert result["valid"] is False
    assert result["status"] == STATUS_OUT_OF_ORDER


def test_processing_is_deterministic(base_packet: dict[str, Any]) -> None:
    first = process_telemetry(base_packet)
    second = process_telemetry(base_packet)

    assert first == second


def test_processor_accepts_ordered_packets(base_packet: dict[str, Any]) -> None:
    processor = TelemetryProcessor()

    for sequence in (1, 2, 3):
        result = processor.process(dict(base_packet, sequence=sequence))
        assert result["valid"] is True, f"sequence {sequence} should be accepted"

    assert processor.last_sequence == 3


def test_processor_detects_out_of_order_packets(base_packet: dict[str, Any]) -> None:
    processor = TelemetryProcessor()

    assert processor.process(dict(base_packet, sequence=5))["valid"] is True
    result = processor.process(dict(base_packet, sequence=3))

    assert result["valid"] is False
    assert result["status"] == STATUS_OUT_OF_ORDER
    assert "sequence 3 is out of order, expected greater than 5" in result["errors"]


def test_processor_keeps_history_when_a_packet_is_rejected(base_packet: dict[str, Any]) -> None:
    processor = TelemetryProcessor()

    processor.process(dict(base_packet, sequence=5))
    processor.process(dict(base_packet, sequence=3))

    assert processor.last_sequence == 5


def test_processor_can_be_seeded_with_a_history(base_packet: dict[str, Any]) -> None:
    processor = TelemetryProcessor(last_sequence=100)

    result = processor.process(dict(base_packet, sequence=100))

    assert result["valid"] is False
    assert result["status"] == STATUS_OUT_OF_ORDER


def test_normalise_telemetry_requires_validated_input(base_packet: dict[str, Any]) -> None:
    normalised = normalise_telemetry(base_packet)

    assert normalised["sequence"] == 1
    assert normalised["status"] == STATUS_PROCESSED


@pytest.mark.parametrize("field", ["timestamp", "sequence", "latitude", "longitude", "altitude", "speed", "battery", "satellites"])
def test_processor_rejects_incomplete_packets(field: str, base_packet: dict[str, Any]) -> None:
    del base_packet[field]

    result = process_telemetry(base_packet)

    assert result["valid"] is False
    assert f"{field} field is required" in result["errors"]
