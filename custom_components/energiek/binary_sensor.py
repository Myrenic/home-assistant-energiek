"""Binary sensors for the Energiek integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import EnergiekDataUpdateCoordinator
from .sensor import EnergiekSensorBase


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Energiek binary sensors."""
    coordinator: EnergiekDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities([EnergiekTomorrowStatusSensor(coordinator)])


class EnergiekTomorrowStatusSensor(EnergiekSensorBase, BinarySensorEntity):
    """Sensor showing if tomorrow's data is available."""

    _attr_name = "Tomorrow Prices Available"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = BinarySensorDeviceClass.UPDATE
    _attr_has_entity_name = False

    def __init__(self, coordinator: EnergiekDataUpdateCoordinator) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_tomorrow_available"

    @property
    def is_on(self) -> bool:
        """Return true if tomorrow's prices are available."""
        return self.coordinator.data.get("tomorrow_available", False)
