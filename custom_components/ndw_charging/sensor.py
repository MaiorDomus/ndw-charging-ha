"""Sensor platform for the NDW Charging Point integration.

Creates one sensor per EVSE found at the configured location.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NdwChargingCoordinator

_LOGGER = logging.getLogger(__name__)

# Standard OCPI v2.2 EVSE status values.
STATUS_ICONS = {
    "AVAILABLE": "mdi:ev-station",
    "CHARGING": "mdi:battery-charging",
    "BLOCKED": "mdi:block-helper",
    "INOPERATIVE": "mdi:close-circle-outline",
    "OUTOFORDER": "mdi:alert-circle",
    "PLANNED": "mdi:calendar-clock",
    "REMOVED": "mdi:delete",
    "RESERVED": "mdi:bookmark",
    "UNKNOWN": "mdi:help-circle",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NdwChargingCoordinator = entry.runtime_data
    evse_ids = [evse["evse_id"] for evse in coordinator.data.get("evses", [])]
    async_add_entities(
        NdwChargePointSensor(coordinator, entry, evse_id) for evse_id in evse_ids
    )


class NdwChargePointSensor(CoordinatorEntity[NdwChargingCoordinator], SensorEntity):
    """Status of a single EVSE (charge point) at an NDW-registered location."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:ev-station"

    def __init__(
        self, coordinator: NdwChargingCoordinator, entry: ConfigEntry, evse_id: str
    ) -> None:
        super().__init__(coordinator)
        self._evse_id = evse_id
        self._attr_unique_id = f"{entry.entry_id}_{evse_id}"

    def _evse(self) -> dict[str, Any] | None:
        for evse in self.coordinator.data.get("evses", []):
            if evse.get("evse_id") == self._evse_id:
                return evse
        return None

    @property
    def available(self) -> bool:
        return super().available and self._evse() is not None

    @property
    def name(self) -> str:
        evse = self._evse()
        ref = evse.get("physical_reference") if evse else None
        return f"Point {ref}" if ref else self._evse_id

    @property
    def native_value(self) -> str | None:
        evse = self._evse()
        return evse.get("status", "UNKNOWN").lower() if evse else None

    @property
    def icon(self) -> str:
        evse = self._evse()
        status = evse.get("status", "UNKNOWN") if evse else "UNKNOWN"
        return STATUS_ICONS.get(status, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        evse = self._evse()
        if not evse:
            return {}
        connector = (evse.get("connectors") or [{}])[0]
        return {
            "evse_id": evse.get("evse_id"),
            "physical_reference": evse.get("physical_reference"),
            "last_updated": evse.get("last_updated"),
            "connector_standard": connector.get("standard"),
            "power_type": connector.get("power_type"),
            "max_voltage": connector.get("max_voltage"),
            "max_amperage": connector.get("max_amperage"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        location = self.coordinator.data
        operator = location.get("operator") or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.location_id)},
            name=location.get("name", self.coordinator.location_id),
            manufacturer=operator.get("name"),
            model="OCPI charging location",
            configuration_url=operator.get("website"),
        )
