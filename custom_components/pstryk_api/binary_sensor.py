"""Binary sensors for Pstryk API"""

from datetime import datetime
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEFAULT_NAME
from .entity import PstrykApiData


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
            async_add_entities: AddEntitiesCallback) -> bool:
    """Setup integration entry"""
    _LOGGER.debug("setting up binary sensors")
    api_data = hass.data[DOMAIN][entry.entry_id]

    entities = [
        PstrykBaseBinarySensor(api_data, "Is Cheap", "is_cheap"),
        PstrykBaseBinarySensor(api_data, "Is Expensive", "is_expensive"),
    ]

    async_add_entities(entities)
    return True


class PstrykBaseBinarySensor(BinarySensorEntity):
    """Base for binary sensor"""
    def __init__(self, api_data: PstrykApiData, name: str, key: str):
        super().__init__()
        _LOGGER.debug("setting up binary sensor %s", name)
        self.api_data = api_data
        self.entity_description = BinarySensorEntityDescription(key=key, name=f"{DEFAULT_NAME} {name}", has_entity_name=True)
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{self.api_data.coordinator.entry.entry_id}_{key}"
        self._attr_device_info = api_data.device

    @property
    def is_on(self):
        """Return the state of the sensor"""
        now_hour = datetime.utcnow().hour
        for frame in self.api_data.coordinator.data["frames"]:
            if datetime.fromisoformat(frame["start"]).hour == now_hour:
                return frame[self.entity_description.key]
        return None


#class PstrykGenericBinarySensor(PstrykBaseBinarySensor):
#    def __init__(self, api_data: PstrykApiData, name: str, key: str):
#        super().__init__(api_data, name, key)
