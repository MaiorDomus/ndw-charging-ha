"""Data update coordinator for the NDW Charging Point integration."""
from __future__ import annotations

import gzip
import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_LOCATION_ID, DATA_URL, DOMAIN, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class LocationNotFound(Exception):
    """Raised when the requested location id isn't in the current NDW feed."""


async def fetch_location(hass: HomeAssistant, location_id: str) -> dict[str, Any]:
    """Download the national feed once and return a single location record.

    Shared by the config flow (to validate a location id up front) and the
    coordinator (for every subsequent poll).
    """
    session = async_get_clientsession(hass)
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    try:
        async with session.get(DATA_URL, timeout=timeout) as resp:
            resp.raise_for_status()
            raw = await resp.read()
    except aiohttp.ClientError as err:
        raise UpdateFailed(f"Error fetching NDW charging point feed: {err}") from err

    def _extract() -> dict[str, Any] | None:
        data = json.loads(gzip.decompress(raw))
        for location in data:
            if location.get("id") == location_id:
                return location
        return None

    location = await hass.async_add_executor_job(_extract)
    if location is None:
        raise LocationNotFound(location_id)
    return location


class NdwChargingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the NDW DOT-NL feed for one charging location."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, update_interval: int
    ) -> None:
        self.location_id = config_entry.data[CONF_LOCATION_ID]
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{self.location_id}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await fetch_location(self.hass, self.location_id)
        except LocationNotFound as err:
            raise UpdateFailed(
                f"Location id {self.location_id} was not found in the NDW feed "
                "(it may have been decommissioned or the id was mistyped)"
            ) from err
