"""
H05 — Normal Input Test Cases
24 October 2026 — Unit Testing

Standalone and directly runnable.
No dependency on the previous TVPS project.

Run:
    python H05_Normal_Input_Test_Cases.py
"""

import json
import unittest


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

REQUIRED_FIELDS = {
    "timestamp",
    "sequence",
    "latitude",
    "longitude",
    "altitude",
    "speed",
    "battery",
    "satellites",
}


def parse_synthetic_data(payload):
    return json.loads(payload)


def validate_synthetic_data(data):
    if not isinstance(data, dict):
        return False

    if not REQUIRED_FIELDS.issubset(data):
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


class TestNormalSyntheticData(unittest.TestCase):

    def test_valid_json_is_parsed(self):
        data = parse_synthetic_data(VALID_TELEMETRY_JSON)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["sequence"], 1)

    def test_required_fields_are_present(self):
        data = parse_synthetic_data(VALID_TELEMETRY_JSON)
        self.assertTrue(REQUIRED_FIELDS.issubset(data.keys()))

    def test_valid_data_types(self):
        data = parse_synthetic_data(VALID_TELEMETRY_JSON)

        self.assertIsInstance(data["timestamp"], str)
        self.assertIsInstance(data["sequence"], int)

        for field in (
            "latitude",
            "longitude",
            "altitude",
            "speed",
            "battery",
            "satellites",
        ):
            self.assertIsInstance(data[field], (int, float))

    def test_valid_data_passes_validation(self):
        data = parse_synthetic_data(VALID_TELEMETRY_JSON)
        self.assertTrue(validate_synthetic_data(data))

    def test_positive_sequence(self):
        data = parse_synthetic_data(VALID_TELEMETRY_JSON)

        for sequence in (1, 2, 10, 100):
            data["sequence"] = sequence
            self.assertTrue(validate_synthetic_data(data))


if __name__ == "__main__":
    unittest.main(verbosity=2)
