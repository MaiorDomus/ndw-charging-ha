"""Shared fixtures for the ndw_charging test suite."""
from __future__ import annotations

import gzip
import json

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ndw_charging loadable in every test."""
    yield


def make_location(
    location_id: str = "NLLOC000001",
    name: str = "NL, Test Street 1, 1234 AB Testtown",
) -> dict:
    """Build a minimal-but-realistic NDW OCPI location record."""
    return {
        "id": location_id,
        "name": name,
        "address": "Test Street 1",
        "city": "Testtown",
        "operator": {"name": "Allego", "website": "https://www.allego.eu"},
        "coordinates": {"latitude": "52.0", "longitude": "5.0"},
        "evses": [
            {
                "evse_id": f"{location_id}-EVSE1",
                "physical_reference": f"{location_id}-1",
                "status": "AVAILABLE",
                "last_updated": "2026-09-13T18:55:00Z",
                "connectors": [
                    {
                        "standard": "IEC_62196_T2",
                        "power_type": "AC_3_PHASE",
                        "max_voltage": 230,
                        "max_amperage": 16,
                    }
                ],
            },
            {
                "evse_id": f"{location_id}-EVSE2",
                "physical_reference": f"{location_id}-2",
                "status": "CHARGING",
                "last_updated": "2026-09-13T18:18:13Z",
                "connectors": [
                    {
                        "standard": "IEC_62196_T2",
                        "power_type": "AC_3_PHASE",
                        "max_voltage": 230,
                        "max_amperage": 16,
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_location() -> dict:
    """A single sample location record (Python dict form)."""
    return make_location()


@pytest.fixture
def sample_feed_bytes(sample_location: dict) -> bytes:
    """The gzip-compressed national feed payload the coordinator downloads."""
    other_location = make_location(location_id="NLLOC999999", name="Somewhere Else")
    feed = [other_location, sample_location]
    return gzip.compress(json.dumps(feed).encode())
