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

from .const import DOMAIN, DEFAULT_NAME, FRAMES, METRICS, PRICING, FULL_PRICE
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

    def get_current_frame(self):
        now = datetime.utcnow()
        for frame in self.api_data.coordinator.data[FRAMES]:
            if datetime.fromisoformat(frame["start"]) <= now < datetime.fromisoformat(frame["end"]):
                return frame
        return None

    def get_current_frame_attribute(self, attr_name):
        frame = self.get_current_frame()
        if not frame:
            return None
        return frame[METRICS][PRICING].get(attr_name)

    def get_metrics_pricing(self, attr_name, start, end):
        ret = []
        for frame in self.api_data.coordinator.data[FRAMES]:
            if today_start <= datetime.fromisoformat(frame["start"]) and datetime.fromisoformat(frame["end"]) <= today_end:
                ret.append(frame[METRICS][PRICING][attr_name])
        return ret

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
        return self.get_current_frame_attribute(FULL_PRICE)

    @property
    def extra_state_attributes(self):
        frame = self.get_current_frame()
        flat_frame = {f"_current_{k}": v for k, v in frame}
        return {**self.api_data.coordinator.data, **flat_frame}


class PstrykPriceMinSensor(PstrykBasePriceSensor):
    """Price Min Sensor"""
    def __init__(self, api_data: PstrykApiData) -> None:
        super().__init__(api_data, "min", "Gross Min")

    @property
    def native_value(self):
        today_start = now.replace(hour=0, minute=0, second=0).astimezone(dateutil.tz.tzlocal())
        today_end = today_start + timedelta(days=1)
        prices = self.get_metrics_pricing(FULL_PRICE, today_start, today_end)
        return min(prices)

class PstrykPriceMaxSensor(PstrykBasePriceSensor):
    """Price Max Sensor"""
    def __init__(self, api_data: PstrykApiData) -> None:
        super().__init__(api_data, "max", "Gross Max")

    @property
    def native_value(self):
        today_start = now.replace(hour=0, minute=0, second=0).astimezone(dateutil.tz.tzlocal())
        today_end = today_start + timedelta(days=1)
        prices = self.get_metrics_pricing(FULL_PRICE, today_start, today_end)
        return max(prices)
