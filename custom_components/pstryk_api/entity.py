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

    @staticmethod
    def parse_data(data):
        """Parse out API data into internal structure"""
        data["_today"] = {}
        data["_tomorrow"] = {}
        today_local = datetime.now().replace(hour=0, minute=0, second=0).astimezone(dateutil.tz.tzlocal())
        tomorrow_local = today_local + timedelta(days=1)
        for frame in data["frames"]:
            start = datetime.fromisoformat(frame["start"]).astimezone(dateutil.tz.tzlocal())
            if start.day == today_local.day:
                data["_today"][start.hour] = frame["price_gross"]
            if start.day == tomorrow_local.day:
                data["_tomorrow"][start.hour] = frame["price_gross"]

        data["_today_min"] = min(data["_today"].values())
        data["_today_max"] = max(data["_today"].values())
        data["_tomorrow_min"] = min(data["_tomorrow"].values())
        data["_tomorrow_max"] = max(data["_tomorrow"].values())
        return data


    async def _async_update_data(self):
        try:
            _LOGGER.debug("calling %s", self.url)
            headers = {"Authorization": self.token, "Accept": "application/json"}
            today = datetime.now().replace(hour=0, minute=0, second=0).astimezone(dateutil.tz.tzutc())
            params = {
                "resolution": "hour",
                "window_start": today.isoformat(),
                "window_end": (today + timedelta(days=2)).isoformat(),
            }
            response = await self.hass.async_add_executor_job(
                partial(requests.get, f"{self.url}/integrations/pricing/", params=params, headers=headers)
            )
            response.raise_for_status()
            self._raw_data = response.json()
            self.data = self.parse_data(self._raw_data)

            return self.data
        except requests.exceptions.RequestException as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex


@dataclass
class PstrykApiData:
    """HA entry class to hold structured data"""
    coordinator: PstrykPricingDataUpdateCoordinator
    device: DeviceInfo
