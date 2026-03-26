"""The ClawHome integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import ClawHomeCoordinator

_LOGGER = logging.getLogger(__name__)

type ClawHomeConfigEntry = ConfigEntry[ClawHomeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ClawHomeConfigEntry) -> bool:
    """Set up ClawHome from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = ClawHomeCoordinator(hass, host, port, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ClawHomeConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: ClawHomeCoordinator = entry.runtime_data
        await coordinator.async_shutdown()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ClawHomeConfigEntry) -> None:
    """Handle options update — recreate coordinator with new scan interval."""
    await hass.config_entries.async_reload(entry.entry_id)
