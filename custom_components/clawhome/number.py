"""Number platform for ClawHome."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up ClawHome numbers."""
    coordinator: ClawHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ClawHomeScanIntervalNumber(coordinator, entry),
    ])


class ClawHomeScanIntervalNumber(CoordinatorEntity[ClawHomeCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Scan Interval"
    _attr_icon = "mdi:timer-cog"
    _attr_native_min_value = 15
    _attr_native_max_value = 120
    _attr_native_step = 5
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: ClawHomeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_scan_interval"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "ClawHome",
        }

    @property
    def native_value(self) -> float:
        if self.coordinator.data:
            return float(self.coordinator.data.interval_minutes)
        return 60.0

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator._post(API_BRAIN_CONFIG, {"intervalMinutes": int(value)})
        await self.coordinator.async_request_refresh()
