"""Config Flow for multi-entry Pstryk API integration"""
from typing import Any

import logging
from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_TOKEN,
)
import voluptuous as vol

from .const import (
    DOMAIN,
)


_LOGGER = logging.getLogger(__name__)

class PstrykAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Pstryk API Config Flow class"""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                  vol.Required(CONF_NAME): str,
                  vol.Required(CONF_TOKEN): str,
                }),
            )

        await self.async_set_unique_id(user_input[CONF_NAME])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
