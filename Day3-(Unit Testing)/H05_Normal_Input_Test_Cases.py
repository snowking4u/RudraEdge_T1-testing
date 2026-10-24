"""H05: synthetic telemetry validator and positive unit tests.

Run from this folder with:
    python H05_Normal_Input_Test_Cases.py

This existing assignment file contains both the small parser/validator module
and its positive tests. H06 imports the same functions for negative tests.
"""

import json
import math
import unittest
from datetime import datetime
from typing import Any


REQUIRED_FIELDS = (
    "timestamp",
    "sequence",
    "latitude",
    "longitude",
    "altitude",
    "speed",
    "battery",
    "satellites",
)

MEASUREMENT_FIELDS = ("latitude", "longitude", "altitude", "speed", "battery")


def parse_synthetic_data(payload: str) -> Any:
    """Decode JSON text; malformed text raises ``json.JSONDecodeError``."""
    return json.loads(payload)


def _is_finite_number(value: Any) -> bool:
    """Accept finite ints/floats, but do not treat booleans as numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return isinstance(value, int) or math.isfinite(value)


def _is_valid_timestamp(value: Any) -> bool:
    """Check for a parseable ISO 8601 timestamp, including UTC ``Z``."""
    if not isinstance(value, str) or not value.strip():
        return False

    normalized_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized_value)
    except ValueError:
        return False
    return True


def validate_synthetic_data(data: Any) -> bool:
    """Validate required telemetry fields, types, and basic value ranges.

    Extra fields are allowed for optional metadata. The rules are:
    - timestamp is a parseable ISO 8601 string
    - sequence and satellites are non-negative integers
    - latitude is between -90 and 90; longitude is between -180 and 180
    - altitude is a finite number; speed is finite and non-negative
    - battery is a finite number from 0 through 100
    """
    if not isinstance(data, dict):
        return False
    if not set(REQUIRED_FIELDS).issubset(data):
        return False
    if not _is_valid_timestamp(data["timestamp"]):
        return False

    sequence = data["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        return False

    for field in MEASUREMENT_FIELDS:
        if not _is_finite_number(data[field]):
            return False

    if not -90 <= data["latitude"] <= 90:
        return False
    if not -180 <= data["longitude"] <= 180:
        return False
    if data["speed"] < 0:
        return False
    if not 0 <= data["battery"] <= 100:
        return False

    satellites = data["satellites"]
    if isinstance(satellites, bool) or not isinstance(satellites, int) or satellites < 0:
        return False

    return True


VALID_TELEMETRY_JSON = """
{
    "timestamp": "2026-10-24T10:00:00Z",
    "sequence": 1,
    "latitude": 31.75,
    "longitude": 76.50,
    "altitude": 100.0,
    "speed": 80.0,
    "battery": 90.0,
    "satellites": 12
}
"""


class TestNormalSyntheticData(unittest.TestCase):
    """Check that representative valid records parse and pass validation."""

    def setUp(self):
        """Parse a fresh copy so one test cannot affect another."""
        self.data = parse_synthetic_data(VALID_TELEMETRY_JSON)

    def test_valid_json_is_parsed_into_a_dictionary(self):
        self.assertIsInstance(self.data, dict)
        self.assertEqual(self.data["sequence"], 1)

    def test_parsed_record_contains_every_required_field(self):
        self.assertTrue(set(REQUIRED_FIELDS).issubset(self.data))

    def test_valid_record_passes_validation(self):
        self.assertTrue(validate_synthetic_data(self.data))

    def test_zero_sequence_is_valid(self):
        self.data["sequence"] = 0
        self.assertTrue(validate_synthetic_data(self.data))

    def test_documented_measurement_boundaries_are_valid(self):
        """Geographic and percentage limits include their endpoints."""
        boundary_values = {
            "latitude": -90,
            "longitude": 180,
            "speed": 0,
            "battery": 100,
            "satellites": 0,
        }

        for field, value in boundary_values.items():
            with self.subTest(field=field, value=value):
                record = dict(self.data)
                record[field] = value
                self.assertTrue(validate_synthetic_data(record))

    def test_optional_extra_fields_are_allowed(self):
        self.data["device_name"] = "demo-unit-01"
        self.assertTrue(validate_synthetic_data(self.data))


if __name__ == "__main__":
    unittest.main(verbosity=2)
