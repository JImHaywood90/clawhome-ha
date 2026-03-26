"""Switch platform for ClawHome."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_BRAIN_CONFIG, DOMAIN
from .coordinator import ClawHomeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ClawHome switches."""
    coordinator: ClawHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ClawHomeBrainSwitch(coordinator, entry),
        ClawHomeAutonomousSwitch(coordinator, entry),
    ])


class ClawHomeBaseSwitch(CoordinatorEntity[ClawHomeCoordinator], SwitchEntity):
    """Base switch for ClawHome."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ClawHomeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "ClawHome",
        }


class ClawHomeBrainSwitch(ClawHomeBaseSwitch):
    _attr_name = "Brain Enabled"
    _attr_icon = "mdi:brain"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_brain_enabled"

    @property
    def is_on(self) -> bool:
        if self.coordinator.data:
            return self.coordinator.data.brain_enabled
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator._post(API_BRAIN_CONFIG, {"enabled": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator._post(API_BRAIN_CONFIG, {"enabled": False})
        await self.coordinator.async_request_refresh()


class ClawHomeAutonomousSwitch(ClawHomeBaseSwitch):
    _attr_name = "Autonomous Actions"
    _attr_icon = "mdi:robot"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_autonomous_actions"

    @property
    def is_on(self) -> bool:
        if self.coordinator.data:
            return self.coordinator.data.autonomous_actions
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator._post(API_BRAIN_CONFIG, {"autonomousActions": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator._post(API_BRAIN_CONFIG, {"autonomousActions": False})
        await self.coordinator.async_request_refresh()
