"""Sensors for Pstryk API"""
# https://developers.home-assistant.io/docs/core/entity/sensor/

import logging
from datetime import datetime, timedelta
from functools import partial
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
#from homeassistant.util import dt as dt_util
import requests
from .const import DOMAIN, MANUFACTURER, DEFAULT_NAME, HOME_URL, DEFAULT_URL


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Setup integration entry"""
    _LOGGER.debug("setting up coordinator for %s", entry)
    coordinator = PstrykPricingDataUpdateCoordinator(hass, entry)
    _LOGGER.debug("awaiting coordinator first refresh %s", entry)
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("assigning coordinator %s", entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    _LOGGER.debug("setting up sensors")

    entities = [
        PstrykPriceSensor(coordinator, "price", "price")
    ]

    async_add_entities(entities)
    return True


class PstrykPricingDataUpdateCoordinator(DataUpdateCoordinator):
    """Pstryk Pricing API polling coordinator"""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        _LOGGER.debug("initializing coordinator: %s", entry)
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            #TODO# pricing really changes (read: shows up) once a day, but want to get data ASAP when it does
            update_interval=timedelta(seconds=7200)
        )
        self.entry = entry
        self.url = DEFAULT_URL
        self.name = entry.data[CONF_NAME]
        self.token = entry.data[CONF_TOKEN]
        self.data = None

    async def _async_update_data(self):
        try:
            _LOGGER.debug("calling %s", self.url)
            headers = {"Authorization": self.token, "Accept": "application/json"}
            params = {
                "resolution": "hour",
                "window_start": "2025-04-13T00:00:00",
                "window_end": "2025-04-14T00:00:00",
            }
            response = await self.hass.async_add_executor_job(partial(requests.get, f"{self.url}/integrations/pricing/", params=params, headers=headers))
            response.raise_for_status()
            self.data = response.json()
            _LOGGER.debug("received %s", self.data)
            return self.data
        except requests.exceptions.RequestException as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex


class PstrykBaseSensor(SensorEntity):
    """Base class with common attributes"""

    def __init__(self, coordinator: DataUpdateCoordinator, src: str, sid: str, name: str) -> None:
        """Initialize sensor with src: json data key, sid: entity id, name: display name"""
        super().__init__()
        _LOGGER.debug("setting up %s", sid)
        self._coordinator = coordinator
        self._podsumowanie_key = src
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{self._coordinator.entry.entry_id}_{sid}"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, coordinator.name)},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
            configuration_url=HOME_URL,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success


class PstrykPriceSensor(PstrykBaseSensor):
    """Price Sensor"""
    def __init__(self, coordinator: DataUpdateCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, key, name)
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = None # SensorStateClass.MEASUREMENT conflicts with MONETARY
        self._attr_native_unit_of_measurement = "zl/kWh"
        self._attr_icon = "mdi:cash"

    @property
    def native_value(self):
        now_hour = datetime.now().hour
        for frame in self._coordinator.data["frames"]:
            if datetime.fromisoformat(frame["start"]).hour == now_hour:
                return frame["price_gross"]
        return None

#    @property
#    def icon(self) -> str:
#        return "mdi:cash"

    @property
    def extra_state_attributes(self):
        return self._coordinator.data
