"""Sensors for Pstryk API"""
# vim: set fileencoding=utf-8
# https://developers.home-assistant.io/docs/core/entity/sensor/

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
#from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_NAME
from .entity import PstrykApiData


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
            async_add_entities: AddEntitiesCallback) -> bool:
    """Setup integration entry"""
    _LOGGER.debug("setting up sensors")
    api_data = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PstrykPriceSensor(api_data, "price", "Gross"),
        PstrykPriceMinSensor(api_data),
        PstrykPriceMaxSensor(api_data),
    ]

    async_add_entities(entities)
    return True


class PstrykBaseSensor(SensorEntity):
    """Base class with common attributes"""

    def __init__(self, api_data: PstrykApiData, sid: str, name: str) -> None:
        """Initialize sensor with src: json data key, sid: entity id, name: display name"""
        super().__init__()
        _LOGGER.debug("setting up sensor %s", sid)
        self.api_data = api_data
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{self.api_data.coordinator.entry.entry_id}_{sid}"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = api_data.device

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.api_data.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        return self.api_data.coordinator.last_update_success


class PstrykBasePriceSensor(PstrykBaseSensor):
    """Base Price Sensor"""
    def __init__(self, api_data: PstrykApiData, key: str, name: str) -> None:
        super().__init__(api_data, key, name)
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = None # SensorStateClass.MEASUREMENT conflicts with MONETARY
        self._attr_native_unit_of_measurement = "zł/kWh"
        self._attr_icon = "mdi:cash"


class PstrykPriceSensor(PstrykBasePriceSensor):
    """Price Sensor"""
    @property
    def native_value(self):
        now_hour = datetime.utcnow().hour
        for frame in self.api_data.coordinator.data["frames"]:
            if datetime.fromisoformat(frame["start"]).hour == now_hour:
                return frame["price_gross"]
        return None

    @property
    def extra_state_attributes(self):
        return self.api_data.coordinator.data


class PstrykPriceMinSensor(PstrykBasePriceSensor):
    """Price Min Sensor"""
    def __init__(self, api_data: PstrykApiData) -> None:
        super().__init__(api_data, "min", "Gross Min")

    @property
    def native_value(self):
        return self.api_data.coordinator.data["_today_min"]


class PstrykPriceMaxSensor(PstrykBasePriceSensor):
    """Price Max Sensor"""
    def __init__(self, api_data: PstrykApiData) -> None:
        super().__init__(api_data, "max", "Gross Max")

    @property
    def native_value(self):
        return self.api_data.coordinator.data["_today_max"]
