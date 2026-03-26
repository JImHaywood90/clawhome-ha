"""Button platform for ClawHome."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_BRAIN_DAILY_REVIEW, API_BRAIN_STATUS, DOMAIN
from .coordinator import ClawHomeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ClawHome buttons."""
    coordinator: ClawHomeCoordinator = entry.runtime_data
    async_add_entities([
        ClawHomeRunBrainButton(coordinator, entry),
        ClawHomeDailyReviewButton(coordinator, entry),
    ])


class ClawHomeBaseButton(CoordinatorEntity[ClawHomeCoordinator], ButtonEntity):
    """Base button for ClawHome."""

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


class ClawHomeRunBrainButton(ClawHomeBaseButton):
    _attr_name = "Run Brain Cycle"
    _attr_icon = "mdi:play-circle"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_run_brain"

    async def async_press(self) -> None:
        await self.coordinator._post(API_BRAIN_STATUS, {"action": "run"})
        await self.coordinator.async_request_refresh()


class ClawHomeDailyReviewButton(ClawHomeBaseButton):
    _attr_name = "Run Daily Review"
    _attr_icon = "mdi:calendar-check"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_daily_review"

    async def async_press(self) -> None:
        await self.coordinator._post(API_BRAIN_DAILY_REVIEW, {})
        await self.coordinator.async_request_refresh()
