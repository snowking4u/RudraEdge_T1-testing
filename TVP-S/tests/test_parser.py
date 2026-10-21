"""Unit tests for the TVPS parser (REQ-001, REQ-006)."""

from __future__ import annotations

import json

import pytest

from tvps import STATUS_PARSED, STATUS_REJECTED, parse_telemetry

VALID_PAYLOAD = json.dumps(
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

MALFORMED_PAYLOADS = [
    pytest.param('{"sequence": 1', id="missing_closing_brace"),
    pytest.param("{'sequence': 1}", id="invalid_quotes"),
    pytest.param('{"sequence": 1,}', id="trailing_comma"),
    pytest.param('{"sequence": ', id="truncated"),
    pytest.param("not json at all", id="not_json"),
    pytest.param('{"a" 1}', id="corrupted_structure"),
    pytest.param('{"sequence": 1}}', id="extra_data"),
]


def test_valid_payload_is_parsed_into_a_telemetry_object() -> None:
    result = parse_telemetry(VALID_PAYLOAD)

    assert result["valid"] is True
    assert result["status"] == STATUS_PARSED
    assert result["errors"] == []
    assert result["error_details"] == []
    assert result["data"] == {
        "timestamp": "2024-05-01T09:00:00Z",
        "sequence": 1,
        "latitude": 12.5,
        "longitude": 45.25,
        "altitude": 120.5,
        "speed": 33.0,
        "battery": 87.5,
        "satellites": 12,
    }


def test_payload_given_as_bytes_is_parsed() -> None:
    result = parse_telemetry(VALID_PAYLOAD.encode("utf-8"))

    assert result["valid"] is True
    assert result["data"]["sequence"] == 1


@pytest.mark.parametrize("raw", MALFORMED_PAYLOADS)
def test_malformed_json_is_rejected_with_a_parse_error(raw: str) -> None:
    result = parse_telemetry(raw)

    assert result["valid"] is False
    assert result["status"] == STATUS_REJECTED
    assert result["data"] is None
    assert result["errors"], "a malformed payload must produce an error message"
    assert result["error_details"][0]["code"] == "PARSE_ERROR"
    assert result["errors"][0].startswith("malformed JSON:")


def test_parse_error_reports_the_failing_position() -> None:
    result = parse_telemetry('{"sequence": ')

    detail = result["error_details"][0]
    assert detail["code"] == "PARSE_ERROR"
    assert detail["context"]["line"] == 1
    assert detail["context"]["column"] > 0


def test_none_input_is_rejected() -> None:
    result = parse_telemetry(None)

    assert result["valid"] is False
    assert result["errors"] == ["telemetry input must not be None"]
    assert result["error_details"][0]["code"] == "EMPTY_INPUT"


@pytest.mark.parametrize("raw", ["", "   ", "\n\t "])
def test_empty_input_is_rejected(raw: str) -> None:
    result = parse_telemetry(raw)

    assert result["valid"] is False
    assert result["errors"] == ["telemetry input must not be empty"]
    assert result["error_details"][0]["code"] == "EMPTY_INPUT"


@pytest.mark.parametrize("raw", [42, 3.5, True, ["a"], {"already": "decoded"}])
def test_unsupported_input_types_are_rejected(raw: object) -> None:
    result = parse_telemetry(raw)  # type: ignore[arg-type]

    assert result["valid"] is False
    assert result["error_details"][0]["code"] == "PARSE_ERROR"
    assert "telemetry input must be a string or bytes" in result["errors"][0]


@pytest.mark.parametrize("raw", ["[1, 2, 3]", '"a string"', "42", "null"])
def test_json_that_is_not_an_object_is_rejected(raw: str) -> None:
    result = parse_telemetry(raw)

    assert result["valid"] is False
    assert result["error_details"][0]["code"] == "PARSE_ERROR"
    assert "telemetry JSON must be an object" in result["errors"][0]


def test_invalid_utf8_bytes_are_rejected() -> None:
    result = parse_telemetry(b"\xff\xfe\x00")

    assert result["valid"] is False
    assert result["error_details"][0]["code"] == "PARSE_ERROR"
    assert "not valid UTF-8" in result["errors"][0]


def test_parsing_is_deterministic() -> None:
    first = parse_telemetry(VALID_PAYLOAD)
    second = parse_telemetry(VALID_PAYLOAD)

    assert first == second


def test_every_malformed_data_file_packet_is_rejected(malformed_packets: list[str]) -> None:
    assert malformed_packets, "the malformed data file must not be empty"

    for raw in malformed_packets:
        result = parse_telemetry(raw)
        assert result["valid"] is False, f"payload should be rejected: {raw!r}"
        assert result["error_details"][0]["code"] in {"PARSE_ERROR", "EMPTY_INPUT"}
