"""Tests for coordinator.fetch_location and NdwChargingCoordinator."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ndw_charging.coordinator import (
    LocationNotFound,
    NdwChargingCoordinator,
    fetch_location,
)


class _FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    def raise_for_status(self) -> None:
        return None

    async def read(self) -> bytes:
        return self._data


class _FakeSession:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def get(self, url, timeout=None):  # noqa: ARG002 - signature mirrors aiohttp
        return _FakeResponse(self._data)


def _patch_session(data: bytes):
    return patch(
        "custom_components.ndw_charging.coordinator.async_get_clientsession",
        return_value=_FakeSession(data),
    )


async def test_fetch_location_found(
    hass: HomeAssistant, sample_feed_bytes: bytes, sample_location: dict
) -> None:
    with _patch_session(sample_feed_bytes):
        location = await fetch_location(hass, sample_location["id"])

    assert location == sample_location


async def test_fetch_location_not_found(hass: HomeAssistant, sample_feed_bytes: bytes) -> None:
    with _patch_session(sample_feed_bytes), pytest.raises(LocationNotFound):
        await fetch_location(hass, "NLLOC_DOES_NOT_EXIST")


async def test_coordinator_update_success(
    hass: HomeAssistant, sample_feed_bytes: bytes, sample_location: dict
) -> None:
    coordinator = NdwChargingCoordinator(hass, sample_location["id"], update_interval=600)

    with _patch_session(sample_feed_bytes):
        await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data == sample_location


async def test_coordinator_update_raises_update_failed_when_missing(
    hass: HomeAssistant, sample_feed_bytes: bytes
) -> None:
    coordinator = NdwChargingCoordinator(hass, "NLLOC_DOES_NOT_EXIST", update_interval=600)

    with _patch_session(sample_feed_bytes):
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
