"""Sensors for the Energiek integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import EnergiekDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Energiek sensors."""
    coordinator: EnergiekDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = [
        EnergiekElectricityPriceSensor(coordinator),
        EnergiekGasPriceSensor(coordinator),
        EnergiekTomorrowStatusSensor(coordinator),
    ]

    async_add_entities(entities)


class EnergiekSensorBase(CoordinatorEntity[EnergiekDataUpdateCoordinator]):
    """Base class for Energiek sensors."""

    def __init__(self, coordinator: EnergiekDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Energiek",
            "manufacturer": "Energiek",
            "model": "Energy Prices",
        }


class EnergiekElectricityPriceSensor(EnergiekSensorBase, SensorEntity):
    """Sensor for electricity prices."""

    _attr_has_entity_name = True
    _attr_name = "Current Electricity Price (All-in)"
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, coordinator: EnergiekDataUpdateCoordinator) -> None:
        """Initialize the electricity sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_electricity_price"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if self.coordinator.data.get("electricity"):
            return self.coordinator.data["electricity"].current_price
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data.get("electricity"):
            # Format prices for apexcharts
            prices = self.coordinator.data["electricity"].prices
            attrs["prices"] = [
                {"from": p["from"].isoformat(), "price": p["price"]}
                for p in prices
            ]
        return attrs


class EnergiekGasPriceSensor(EnergiekSensorBase, SensorEntity):
    """Sensor for gas prices."""

    _attr_has_entity_name = True
    _attr_name = "Current Gas Price (All-in)"
    _attr_native_unit_of_measurement = "EUR/m³"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fire"

    def __init__(self, coordinator: EnergiekDataUpdateCoordinator) -> None:
        """Initialize the gas sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_gas_price"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if self.coordinator.data.get("gas"):
            return self.coordinator.data["gas"].current_price
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data.get("gas"):
            # Format prices for apexcharts
            prices = self.coordinator.data["gas"].prices
            attrs["prices"] = [
                {"from": p["from"].isoformat(), "price": p["price"]}
                for p in prices
            ]
        return attrs


class EnergiekTomorrowStatusSensor(EnergiekSensorBase, BinarySensorEntity):
    """Sensor showing if tomorrow's data is available."""

    _attr_has_entity_name = True
    _attr_name = "Tomorrow Prices Available"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = BinarySensorDeviceClass.UPDATE

    def __init__(self, coordinator: EnergiekDataUpdateCoordinator) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_tomorrow_available"

    @property
    def is_on(self) -> bool:
        """Return true if tomorrow's prices are available."""
        return self.coordinator.data.get("tomorrow_available", False)
