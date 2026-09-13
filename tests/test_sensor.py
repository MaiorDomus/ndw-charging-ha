"""Tests for setting up the integration and its sensors."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from custom_components.ndw_charging.const import CONF_LOCATION_ID, DOMAIN
from custom_components.ndw_charging.coordinator import LocationNotFound
from pytest_homeassistant_custom_component.common import MockConfigEntry


def _patch_fetch_location(**kwargs):
    return patch(
        "custom_components.ndw_charging.coordinator.fetch_location",
        AsyncMock(**kwargs),
    )


async def _setup_entry(hass: HomeAssistant, sample_location: dict) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=sample_location["id"],
        data={CONF_LOCATION_ID: sample_location["id"]},
    )
    entry.add_to_hass(hass)

    with _patch_fetch_location(return_value=sample_location):
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_creates_one_sensor_per_evse(
    hass: HomeAssistant, sample_location: dict
) -> None:
    entry = await _setup_entry(hass, sample_location)

    assert entry.state is ConfigEntryState.LOADED
    states = hass.states.async_all("sensor")
    assert len(states) == len(sample_location["evses"])
    assert sorted(s.state for s in states) == ["available", "charging"]


async def test_sensor_attributes_reflect_the_evse(
    hass: HomeAssistant, sample_location: dict
) -> None:
    await _setup_entry(hass, sample_location)

    charging_evse = next(
        e for e in sample_location["evses"] if e["status"] == "CHARGING"
    )
    state = next(
        s
        for s in hass.states.async_all("sensor")
        if s.attributes["evse_id"] == charging_evse["evse_id"]
    )

    assert state.state == "charging"
    assert state.attributes["physical_reference"] == charging_evse["physical_reference"]
    assert state.attributes["last_updated"] == charging_evse["last_updated"]
    assert state.attributes["connector_standard"] == "IEC_62196_T2"


async def test_sensors_become_unavailable_when_update_fails(
    hass: HomeAssistant, sample_location: dict
) -> None:
    entry = await _setup_entry(hass, sample_location)

    with _patch_fetch_location(side_effect=LocationNotFound(sample_location["id"])):
        await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    states = hass.states.async_all("sensor")
    assert all(s.state == STATE_UNAVAILABLE for s in states)


async def test_unload_entry_removes_sensors(
    hass: HomeAssistant, sample_location: dict
) -> None:
    entry = await _setup_entry(hass, sample_location)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert all(
        s.state == STATE_UNAVAILABLE for s in hass.states.async_all("sensor")
    )
