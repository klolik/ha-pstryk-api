"""The Pstryk API component."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType

from .const import DOMAIN, MANUFACTURER, DEFAULT_NAME, HOME_URL
from .entity import PstrykPricingDataUpdateCoordinator, PstrykApiData


PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Setup the integration"""
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup config entry"""
    _LOGGER.debug("setting up coordinator for %s", entry)
    coordinator = PstrykPricingDataUpdateCoordinator(hass, entry)

    _LOGGER.debug("awaiting coordinator first refresh %s", entry)
    await coordinator.async_config_entry_first_refresh()

    # common device shared across sensors
    device = DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, coordinator.name)},
        manufacturer=MANUFACTURER,
        name=DEFAULT_NAME,
        configuration_url=HOME_URL,
    )

    hass.data[DOMAIN][entry.entry_id] = PstrykApiData(coordinator, device)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry"""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
