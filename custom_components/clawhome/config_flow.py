"""Config flow for ClawHome integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    API_INFO,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
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

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._name: str = "ClawHome"

    async def async_step_zeroconf(self, discovery_info: Any) -> FlowResult:
        """Handle zeroconf discovery."""
        self._host = str(discovery_info.host)
        self._port = discovery_info.port or DEFAULT_PORT
        self._name = discovery_info.name.split(".")[0]

        await self.async_set_unique_id(f"clawhome_{self._host}_{self._port}")
        self._abort_if_unique_id_configured()

        info = await _validate_connection(self._host, self._port)
        if not info:
            return self.async_abort(reason="cannot_connect")

        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm zeroconf discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._name,
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                },
                options={
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                },
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "host": self._host,
                "port": str(self._port),
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return ClawHomeOptionsFlow()


class ClawHomeOptionsFlow(OptionsFlow):
    """Handle options for ClawHome."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        int, vol.Range(min=10, max=120)
                    ),
                }
            ),
        )
