"""Shared fixtures for the TVPS verification suite.

The fixtures load the deterministic demonstration data so that the tests
never depend on hand written duplicates of the data files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# Make the project importable when pytest is started from another folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tvps import load_cases, load_raw_packets  # noqa: E402
from tvps.app.service import DATA_DIR  # noqa: E402

BASE_PACKET: dict[str, Any] = {
    "timestamp": "2024-05-01T09:00:00Z",
    "sequence": 1,
    "latitude": 12.5,
    "longitude": 45.25,
    "altitude": 120.5,
    "speed": 33.0,
    "battery": 87.5,
    "satellites": 12,
}


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Return the directory holding the deterministic demonstration data."""
    return DATA_DIR


@pytest.fixture(scope="session")
def valid_cases() -> list[dict[str, Any]]:
    """Return every valid telemetry case of the data file."""
    return load_cases(DATA_DIR / "valid_telemetry.json")


@pytest.fixture(scope="session")
def invalid_cases() -> list[dict[str, Any]]:
    """Return every invalid telemetry case of the data file."""
    return load_cases(DATA_DIR / "invalid_telemetry.json")


@pytest.fixture(scope="session")
def malformed_packets() -> list[str]:
    """Return every malformed raw payload of the data file."""
    return load_raw_packets(DATA_DIR / "malformed_packets.txt")


@pytest.fixture()
def base_packet() -> dict[str, Any]:
    """Return a fresh copy of a valid telemetry packet."""
    return dict(BASE_PACKET)
