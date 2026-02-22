"""The Energiek component."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DATA_API, DATA_COORDINATOR, DOMAIN
from .coordinator import EnergiekDataUpdateCoordinator
from .energiek_api import EnergiekAPI, AuthException

PLATFORMS = ["sensor", "binary_sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energiek from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    api = EnergiekAPI()
    try:
        await api.login(email, password)
    except AuthException as ex:
        _LOGGER.error("Failed to login to Energiek: %s", ex)
        return False
    except Exception as ex:
        _LOGGER.error("Unexpected error to login to Energiek: %s", ex)
        return False

    coordinator = EnergiekDataUpdateCoordinator(hass, entry, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_API: api,
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        api = data[DATA_API]
        await api.__aexit__(None, None, None)

    return unload_ok
