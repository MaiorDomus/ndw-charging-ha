"""The NDW Charging Point (DOT-NL) integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .coordinator import NdwChargingCoordinator

PLATFORMS = ["sensor"]

# entry.runtime_data holds the NdwChargingCoordinator for this entry - the
# current recommended alternative to hass.data[DOMAIN][entry.entry_id].


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    coordinator = NdwChargingCoordinator(hass, entry, update_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
