"""Sensor platform for ClawHome."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClawHomeCoordinator, ClawHomeData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ClawHome sensors."""
    coordinator: ClawHomeCoordinator = entry.runtime_data

    entities: list[SensorEntity] = [
        ClawHomeBrainStatusSensor(coordinator, entry),
        ClawHomeLastReasoningSensor(coordinator, entry),
        ClawHomeCycleCountSensor(coordinator, entry),
        ClawHomeLastRunSensor(coordinator, entry),
        ClawHomeActiveRulesSensor(coordinator, entry),
        ClawHomePendingRulesSensor(coordinator, entry),
        ClawHomeEventBrainSensor(coordinator, entry),
    ]

    # Dynamic room presence sensors
    if coordinator.data:
        for room_id, room_data in coordinator.data.rooms.items():
            entities.append(
                ClawHomeRoomPresenceSensor(coordinator, entry, room_id, room_data["name"])
            )

    async_add_entities(entities)

    # Track new rooms appearing in future updates
    known_rooms: set[str] = set(coordinator.data.rooms.keys()) if coordinator.data else set()

    @callback
    def _async_check_new_rooms() -> None:
        nonlocal known_rooms
        if not coordinator.data:
            return
        new_rooms = set(coordinator.data.rooms.keys()) - known_rooms
        if new_rooms:
            new_entities = []
            for room_id in new_rooms:
                room_data = coordinator.data.rooms[room_id]
                new_entities.append(
                    ClawHomeRoomPresenceSensor(coordinator, entry, room_id, room_data["name"])
                )
            known_rooms.update(new_rooms)
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_check_new_rooms))


class ClawHomeBaseSensor(CoordinatorEntity[ClawHomeCoordinator], SensorEntity):
    """Base sensor for ClawHome."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ClawHomeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "ClawHome",
            "manufacturer": "ClawHome",
            "model": "AI Smart Home Brain",
            "sw_version": "0.1.0",
        }


class ClawHomeBrainStatusSensor(ClawHomeBaseSensor):
    _attr_name = "Brain Status"
    _attr_icon = "mdi:brain"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_brain_status"

    @property
    def native_value(self) -> str:
        if self.coordinator.data:
            return self.coordinator.data.brain_status
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data:
            return {"running": self.coordinator.data.brain_running}
        return {}


class ClawHomeLastReasoningSensor(ClawHomeBaseSensor):
    _attr_name = "Last Reasoning"
    _attr_icon = "mdi:head-lightbulb"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_last_reasoning"

    @property
    def native_value(self) -> str:
        if self.coordinator.data:
            return self.coordinator.data.last_reasoning or "No reasoning yet"
        return "unknown"


class ClawHomeCycleCountSensor(ClawHomeBaseSensor):
    _attr_name = "Cycle Count"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_cycle_count"

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return self.coordinator.data.cycle_count
        return 0


class ClawHomeLastRunSensor(ClawHomeBaseSensor):
    _attr_name = "Last Run"
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = "timestamp"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_last_run"

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data:
            return self.coordinator.data.last_run
        return None


class ClawHomeActiveRulesSensor(ClawHomeBaseSensor):
    _attr_name = "Active Rules"
    _attr_icon = "mdi:format-list-checks"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_active_rules"

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return self.coordinator.data.active_rules_count
        return 0


class ClawHomePendingRulesSensor(ClawHomeBaseSensor):
    _attr_name = "Pending Rules"
    _attr_icon = "mdi:clock-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_pending_rules"

    @property
    def native_value(self) -> int:
        if self.coordinator.data:
            return self.coordinator.data.pending_rules_count
        return 0


class ClawHomeEventBrainSensor(ClawHomeBaseSensor):
    _attr_name = "Event Brain"
    _attr_icon = "mdi:lightning-bolt"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_event_brain"

    @property
    def native_value(self) -> str:
        if self.coordinator.data:
            return "connected" if self.coordinator.data.event_brain_connected else "disconnected"
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data:
            return {"event_count": self.coordinator.data.event_count}
        return {}


class ClawHomeRoomPresenceSensor(ClawHomeBaseSensor):
    _attr_icon = "mdi:motion-sensor"

    def __init__(
        self,
        coordinator: ClawHomeCoordinator,
        entry: ConfigEntry,
        room_id: str,
        room_name: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._room_id = room_id
        self._room_name = room_name
        self._attr_name = f"{room_name} Presence"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._room_id}_presence"

    @property
    def native_value(self) -> str:
        if self.coordinator.data and self._room_id in self.coordinator.data.rooms:
            return self.coordinator.data.rooms[self._room_id]["confidence"]
        return "none"

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data and self._room_id in self.coordinator.data.rooms:
            return {"occupied": self.coordinator.data.rooms[self._room_id]["occupied"]}
        return {}
