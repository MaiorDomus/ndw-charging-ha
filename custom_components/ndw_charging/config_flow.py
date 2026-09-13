"""Config flow for the NDW Charging Point integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    CONF_LOCATION_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
)
from .coordinator import LocationNotFound, fetch_location

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LOCATION_ID): str,
    }
)


class NdwChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a single NDW charging location."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            location_id = user_input[CONF_LOCATION_ID].strip().upper()
            await self.async_set_unique_id(location_id)
            self._abort_if_unique_id_configured()

            try:
                location = await fetch_location(self.hass, location_id)
            except LocationNotFound:
                errors["base"] = "location_not_found"
            except UpdateFailed:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating NDW location id %s", location_id)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=location.get("name", location_id),
                    data={CONF_LOCATION_ID: location_id},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "NdwChargingOptionsFlow":
        return NdwChargingOptionsFlow()


class NdwChargingOptionsFlow(config_entries.OptionsFlow):
    """Let the update interval be tuned after setup.

    No __init__ override: since HA 2025.12, `config_entry` is a read-only
    property the framework populates itself after construction - assigning
    to it (the old boilerplate pattern) raises AttributeError.
    """

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(int, vol.Range(min=MIN_UPDATE_INTERVAL)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
