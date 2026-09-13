"""Tests for the ndw_charging config flow."""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.ndw_charging.const import CONF_LOCATION_ID, DOMAIN
from custom_components.ndw_charging.coordinator import LocationNotFound
from pytest_homeassistant_custom_component.common import MockConfigEntry


def _patch_fetch_location(**kwargs):
    return patch(
        "custom_components.ndw_charging.config_flow.fetch_location",
        AsyncMock(**kwargs),
    )


async def test_user_flow_creates_entry(hass: HomeAssistant, sample_location: dict) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    # A successful flow makes Home Assistant immediately set up the new
    # entry, which goes through the coordinator's own fetch_location call -
    # so both call sites need mocking, not just the config flow's.
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.ndw_charging.config_flow.fetch_location",
                AsyncMock(return_value=sample_location),
            )
        )
        stack.enter_context(
            patch(
                "custom_components.ndw_charging.coordinator.fetch_location",
                AsyncMock(return_value=sample_location),
            )
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LOCATION_ID: sample_location["id"].lower()}
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == sample_location["name"]
    # Lowercase input is normalized to the feed's uppercase id.
    assert result["data"] == {CONF_LOCATION_ID: sample_location["id"]}


async def test_user_flow_location_not_found(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_fetch_location(side_effect=LocationNotFound("NLLOC000001")):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LOCATION_ID: "NLLOC000001"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "location_not_found"}


async def test_user_flow_aborts_on_duplicate_location(
    hass: HomeAssistant, sample_location: dict
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=sample_location["id"],
        data={CONF_LOCATION_ID: sample_location["id"]},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with _patch_fetch_location(return_value=sample_location):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_LOCATION_ID: sample_location["id"]}
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
