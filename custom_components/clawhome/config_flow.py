"""Config flow for ClawHome integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.core import callback

from .const import (
    API_INFO,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_connection(host: str, port: int) -> dict | None:
    """Validate we can connect to ClawHome and return info."""
    url = f"http://{host}:{port}{API_INFO}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok") and data.get("name") == "ClawHome":
                        return data
    except Exception:
        pass
    return None


class ClawHomeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ClawHome."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle manual configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            info = await _validate_connection(host, port)
            if info:
                await self.async_set_unique_id(f"clawhome_{host}_{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="ClawHome",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
