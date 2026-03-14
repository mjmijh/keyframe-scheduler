"""Switch platform for Keyframe Scheduler - per-light follow switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_FOLLOW_LIGHTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Keyframe Scheduler follow switches."""
    follow_lights = entry.options.get(CONF_FOLLOW_LIGHTS, [])

    entities = [
        KeyframeFollowSwitch(entry, light_entity_id)
        for light_entity_id in follow_lights
    ]

    if entities:
        async_add_entities(entities)


class KeyframeFollowSwitch(SwitchEntity, RestoreEntity):
    """Follow switch for a single light within a Keyframe Scheduler instance.

    Created automatically for each light listed in the instance's follow_lights
    option. State persists across HA restarts via RestoreEntity.

    Entity ID pattern: switch.keyframe_{instance}_{light_slug}_follow
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:lightbulb-auto"

    def __init__(self, entry: ConfigEntry, light_entity_id: str) -> None:
        """Initialize the follow switch."""
        self._entry = entry
        self._light_entity_id = light_entity_id

        # "light.besprechungsraum_1" → "besprechungsraum_1"
        light_slug = light_entity_id.split(".", 1)[-1]

        self._attr_unique_id = f"{entry.entry_id}_{light_entity_id}_follow"
        self._attr_name = f"{light_slug} follow"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Keyframe Scheduler",
            model="Light Schedule Controller",
        )
        self._is_on: bool = True  # Default: following enabled

    async def async_added_to_hass(self) -> None:
        """Restore state after HA restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_on = last_state.state == "on"
            _LOGGER.debug(
                "Restored follow switch %s → %s",
                self._light_entity_id,
                last_state.state,
            )

    @property
    def is_on(self) -> bool:
        """Return True if the light is following the scheduler."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose which light this switch controls."""
        return {
            "light_entity_id": self._light_entity_id,
            "instance": self._entry.title,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable scheduler following."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable scheduler following (manual override)."""
        self._is_on = False
        self.async_write_ha_state()
