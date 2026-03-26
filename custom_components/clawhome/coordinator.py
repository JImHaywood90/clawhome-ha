"""DataUpdateCoordinator for ClawHome."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BRAIN_CONFIG,
    API_BRAIN_STATUS,
    API_ROOMS,
    API_RULES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ClawHomeData:
    """Parsed data from ClawHome APIs."""

    def __init__(self) -> None:
        self.brain_enabled: bool = False
        self.brain_running: bool = False
        self.brain_status: str = "unknown"
        self.last_reasoning: str = ""
        self.cycle_count: int = 0
        self.last_run: str | None = None
        self.event_brain_connected: bool = False
        self.event_count: int = 0
        self.autonomous_actions: bool = False
        self.interval_minutes: int = 60
        self.rooms: dict[str, dict[str, Any]] = {}
        self.active_rules_count: int = 0
        self.pending_rules_count: int = 0


class ClawHomeCoordinator(DataUpdateCoordinator[ClawHomeData]):
    """Coordinator to poll ClawHome APIs."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        scan_interval: int = 30,
    ) -> None:
        self.base_url = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _fetch(self, path: str) -> dict:
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching {path}: {err}") from err

    async def _post(self, path: str, data: dict | None = None) -> dict:
        """POST to ClawHome API (used by entities for commands)."""
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        async with session.post(url, json=data or {}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _async_update_data(self) -> ClawHomeData:
        """Fetch all data from ClawHome."""
        data = ClawHomeData()

        try:
            # Brain status
            brain = await self._fetch(API_BRAIN_STATUS)
            data.brain_enabled = brain.get("enabled", False)
            data.brain_running = brain.get("running", False)
            data.cycle_count = brain.get("cycleCount", 0)
            data.last_run = brain.get("lastRun")
            last_result = brain.get("lastResult") or {}
            data.last_reasoning = (last_result.get("reasoning") or "")[:255]

            # Derive brain status enum
            if not data.brain_enabled:
                data.brain_status = "disabled"
            elif data.brain_running:
                data.brain_status = "thinking"
            elif last_result.get("error"):
                data.brain_status = "error"
            else:
                data.brain_status = "idle"

            # Event brain
            eb = brain.get("eventBrain") or {}
            data.event_brain_connected = eb.get("connected", False)
            data.event_count = eb.get("eventCount", 0)

            # Brain config
            config = await self._fetch(API_BRAIN_CONFIG)
            cfg = config.get("config") or {}
            data.autonomous_actions = cfg.get("autonomousActions", False)
            data.interval_minutes = cfg.get("intervalMinutes", 60)

            # Rooms/presence
            rooms_data = await self._fetch(API_ROOMS)
            presence = rooms_data.get("presence") or {}
            for room_id, room_presence in presence.items():
                data.rooms[room_id] = {
                    "name": room_presence.get("room", room_id),
                    "confidence": room_presence.get("confidence", "none"),
                    "occupied": room_presence.get("occupied", False),
                }

            # Rules counts
            active = await self._fetch(f"{API_RULES}?status=active")
            pending = await self._fetch(f"{API_RULES}?status=pending_approval")
            data.active_rules_count = len(active) if isinstance(active, list) else 0
            data.pending_rules_count = len(pending) if isinstance(pending, list) else 0

        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        return data

    async def async_shutdown(self) -> None:
        """Clean up session."""
        if self._session and not self._session.closed:
            await self._session.close()
