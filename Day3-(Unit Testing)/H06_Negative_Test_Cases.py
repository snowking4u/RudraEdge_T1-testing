"""H06: negative unit tests for invalid synthetic telemetry data.

Run from this folder with:
    python H06_Negative_Test_Cases.py

The tests cover missing fields, wrong types, invalid values, non-object JSON,
and malformed JSON text.
"""

import json
import unittest

from H05_Normal_Input_Test_Cases import (
    REQUIRED_FIELDS,
    parse_synthetic_data,
    validate_synthetic_data,
)


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


class TestNegativeSyntheticData(unittest.TestCase):
    """Confirm invalid records are rejected for the expected reason."""

    def setUp(self):
        self.valid_data = parse_synthetic_data(VALID_TELEMETRY_JSON)

    def test_each_missing_required_field_is_rejected(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(missing_field=field):
                record = dict(self.valid_data)
                record.pop(field)
                self.assertFalse(validate_synthetic_data(record))

    def test_wrong_field_types_are_rejected(self):
        invalid_values = {
            "timestamp": 20261024,
            "sequence": "1",
            "latitude": "31.75",
            "longitude": "76.50",
            "altitude": "100.0",
            "speed": "80.0",
            "battery": "90.0",
            "satellites": 12.5,
        }

        for field, invalid_value in invalid_values.items():
            with self.subTest(field=field, invalid_value=invalid_value):
                record = dict(self.valid_data)
                record[field] = invalid_value
                self.assertFalse(validate_synthetic_data(record))

    def test_invalid_timestamp_is_rejected(self):
        record = dict(self.valid_data)
        record["timestamp"] = "yesterday morning"
        self.assertFalse(validate_synthetic_data(record))

    def test_out_of_range_measurements_are_rejected(self):
        invalid_values = {
            "latitude": 91,
            "longitude": -181,
            "speed": -1,
            "battery": 101,
            "satellites": -1,
            "sequence": -1,
        }

        for field, invalid_value in invalid_values.items():
            with self.subTest(field=field, invalid_value=invalid_value):
                record = dict(self.valid_data)
                record[field] = invalid_value
                self.assertFalse(validate_synthetic_data(record))

    def test_boolean_values_are_not_accepted_as_numbers(self):
        for field in ("sequence", "latitude", "satellites"):
            with self.subTest(field=field):
                record = dict(self.valid_data)
                record[field] = True
                self.assertFalse(validate_synthetic_data(record))

    def test_non_finite_measurements_are_rejected(self):
        for invalid_value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid_value=invalid_value):
                record = dict(self.valid_data)
                record["speed"] = invalid_value
                self.assertFalse(validate_synthetic_data(record))

    def test_valid_json_that_is_not_an_object_is_rejected(self):
        for payload in ("[]", '"telemetry"', "null"):
            with self.subTest(payload=payload):
                decoded_value = parse_synthetic_data(payload)
                self.assertFalse(validate_synthetic_data(decoded_value))

    def test_malformed_json_raises_a_parse_error(self):
        malformed_inputs = (
            '{"timestamp": "2026-10-24T10:00:00Z"',
            '{"sequence": 1, "latitude": 31.75,}',
            '{"timestamp": "2026-10-24T10:00:00Z",',
            '{"sequence": 1, "battery": }',
            '{"timestamp": "missing quote}',
        )

        for payload in malformed_inputs:
            with self.subTest(payload=payload):
                with self.assertRaises(json.JSONDecodeError):
                    parse_synthetic_data(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
