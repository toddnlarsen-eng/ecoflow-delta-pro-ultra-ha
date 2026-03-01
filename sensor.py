"""Sensor platform for EcoFlow Delta Pro Ultra."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_SN,
    DOMAIN,
    SENSOR_DEFINITIONS,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)

# Map string device classes to SensorDeviceClass enum (HA 2023+)
_DEVICE_CLASS_MAP = {
    "battery": SensorDeviceClass.BATTERY,
    "current": SensorDeviceClass.CURRENT,
    "energy": SensorDeviceClass.ENERGY,
    "energy_storage": SensorDeviceClass.ENERGY_STORAGE,
    "frequency": SensorDeviceClass.FREQUENCY,
    "power": SensorDeviceClass.POWER,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "voltage": SensorDeviceClass.VOLTAGE,
}

_STATE_CLASS_MAP = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow sensors."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    data_holder = entry_data["data_holder"]
    device_sn = entry.data[CONF_DEVICE_SN]

    sensors = [
        EcoFlowSensor(
            entry=entry,
            data_holder=data_holder,
            attr_key=attr_key,
            name=name,
            unit=unit,
            device_class_str=device_class_str,
            state_class_str=state_class_str,
            icon=icon,
            device_sn=device_sn,
        )
        for attr_key, name, unit, device_class_str, state_class_str, icon in SENSOR_DEFINITIONS
    ]
    async_add_entities(sensors)


class EcoFlowSensor(SensorEntity):
    """Represents a single EcoFlow Delta Pro Ultra sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        data_holder,
        attr_key: str,
        name: str,
        unit: str | None,
        device_class_str: str | None,
        state_class_str: str | None,
        icon: str | None,
        device_sn: str,
    ) -> None:
        self._entry = entry
        self._data_holder = data_holder
        self._attr_key = attr_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = _DEVICE_CLASS_MAP.get(device_class_str) if device_class_str else None
        self._attr_state_class = _STATE_CLASS_MAP.get(state_class_str) if state_class_str else None
        self._attr_icon = icon
        self._device_sn = device_sn
        self._attr_unique_id = f"{DOMAIN}_{device_sn}_{attr_key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_sn)},
            name=f"EcoFlow Delta Pro Ultra ({self._device_sn})",
            manufacturer="EcoFlow",
            model="Delta Pro Ultra",
            serial_number=self._device_sn,
        )

    @property
    def native_value(self) -> Any:
        return self._data_holder.get(self._attr_key)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
