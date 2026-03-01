"""Number platform for EcoFlow Delta Pro Ultra."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_SN,
    DOMAIN,
    NUMBER_DEFINITIONS,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    data_holder = entry_data["data_holder"]
    mqtt_client = entry_data["mqtt_client"]
    device_sn = entry.data[CONF_DEVICE_SN]

    numbers = [
        EcoFlowNumber(
            entry=entry,
            data_holder=data_holder,
            mqtt_client=mqtt_client,
            attr_key=attr_key,
            name=name,
            unit=unit,
            min_value=min_value,
            max_value=max_value,
            step=step,
            icon=icon,
            mode=mode,
            device_sn=device_sn,
        )
        for attr_key, name, unit, min_value, max_value, step, icon, mode in NUMBER_DEFINITIONS
    ]
    async_add_entities(numbers)


class EcoFlowNumber(NumberEntity):
    """Represents a configurable numeric parameter on the EcoFlow Delta Pro Ultra."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        data_holder,
        mqtt_client,
        attr_key: str,
        name: str,
        unit: str | None,
        min_value: float,
        max_value: float,
        step: float,
        icon: str | None,
        mode: str,
        device_sn: str,
    ) -> None:
        self._entry = entry
        self._data_holder = data_holder
        self._mqtt_client = mqtt_client
        self._attr_key = attr_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_icon = icon
        self._attr_mode = NumberMode.SLIDER if mode == "slider" else NumberMode.BOX
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
    def native_value(self) -> float | None:
        val = self._data_holder.get(self._attr_key)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.hass.async_add_executor_job(
            self._mqtt_client.set_param, self._attr_key, value
        )

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
