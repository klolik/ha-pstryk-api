"""Entity for Pstryk API"""

from dataclasses import dataclass
from functools import partial
from datetime import datetime, timedelta
import logging
import requests

import dateutil.tz

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_NAME,
    CONF_TOKEN,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_URL


_LOGGER = logging.getLogger(__name__)


class PstrykPricingDataUpdateCoordinator(DataUpdateCoordinator):
    """Pstryk Pricing API polling coordinator"""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        _LOGGER.debug("initializing coordinator: %s", entry)
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            #TODO# pricing never really changes, it's announced once a day, but want to get data ASAP when it does
            update_interval=timedelta(seconds=7200)
        )
        self.entry = entry
        self.url = DEFAULT_URL
        self.name = entry.data[CONF_NAME]
        self.token = entry.data[CONF_TOKEN]
        self.data = None
        self._raw_data = None

    async def _async_update_data(self):
        try:
            _LOGGER.debug("calling %s", self.url)
            headers = {"Authorization": self.token, "Accept": "application/json"}
            today = datetime.now().replace(hour=0, minute=0, second=0).astimezone(dateutil.tz.tzutc())
            params = {
                "resolution": "hour",
                "window_start": today,
                "window_end": today + timedelta(days=1),
            }
            response = await self.hass.async_add_executor_job(
                partial(requests.get, f"{self.url}/integrations/pricing/", params=params, headers=headers)
            )
            response.raise_for_status()
            self._raw_data = response.json()
            self.data = self._raw_data

            self.data["_hourly"] = {}
            for frame in self.data["frames"]:
                hour = datetime.fromisoformat(frame["start"]).astimezone(dateutil.tz.tzlocal()).hour
                self.data["_hourly"][hour] = frame["price_gross"]
            _LOGGER.debug("received %s", self.data)
            return self.data
        except requests.exceptions.RequestException as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex


@dataclass
class PstrykApiData:
    """HA entry class to hold structured data"""
    coordinator: PstrykPricingDataUpdateCoordinator
    device: DeviceInfo
