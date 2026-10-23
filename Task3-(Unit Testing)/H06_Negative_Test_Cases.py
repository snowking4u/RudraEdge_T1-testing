"""
H06 — Negative Test Cases
24 October 2026 — Unit Testing

Standalone and directly runnable.
No dependency on the previous TVPS project.

Negative cases:
- Missing fields
- Invalid data types
- Malformed input

Run:
    python H06_Negative_Test_Cases.py
"""

import json
import unittest


VALID_DATA = {
    "timestamp": "2026-10-24T10:00:00Z",
    "sequence": 1,
    "latitude": 31.75,
    "longitude": 76.50,
    "altitude": 100.0,
    "speed": 80.0,
    "battery": 90.0,
    "satellites": 12,
}

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


def parse_synthetic_data(payload):
    return json.loads(payload)


def validate_synthetic_data(data):
    if not isinstance(data, dict):
        return False

    for field in REQUIRED_FIELDS:
        if field not in data:
            return False

    if not isinstance(data["timestamp"], str):
        return False

    if not isinstance(data["sequence"], int) or isinstance(data["sequence"], bool):
        return False

    for field in (
        "latitude",
        "longitude",
        "altitude",
        "speed",
        "battery",
        "satellites",
    ):
        if not isinstance(data[field], (int, float)) or isinstance(data[field], bool):
            return False

    return True


class TestNegativeSyntheticData(unittest.TestCase):

    def test_missing_required_fields_are_rejected(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                data = dict(VALID_DATA)
                data.pop(field)
                self.assertFalse(validate_synthetic_data(data))

    def test_invalid_data_types_are_rejected(self):
        invalid_cases = {
            "timestamp": 12345,
            "sequence": "1",
            "latitude": "31.75",
            "longitude": "76.50",
            "altitude": "100.0",
            "speed": "80.0",
            "battery": "90.0",
            "satellites": "12",
        }

        for field, invalid_value in invalid_cases.items():
            with self.subTest(field=field):
                data = dict(VALID_DATA)
                data[field] = invalid_value
                self.assertFalse(validate_synthetic_data(data))

    def test_malformed_json_is_rejected(self):
        malformed_inputs = [
            '{"timestamp": "2026-10-24T10:00:00Z"',
            '{"sequence": 1, "latitude": 31.75,}',
            '{"timestamp": "2026-10-24T10:00:00Z",',
            '{"sequence": 1, "battery": }',
            '{"timestamp": "missing quote}',
        ]

        for payload in malformed_inputs:
            with self.subTest(payload=payload):
                with self.assertRaises(json.JSONDecodeError):
                    parse_synthetic_data(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
