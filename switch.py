"""Switch platform for EcoFlow Delta Pro Ultra."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_SN,
    DOMAIN,
    SWITCH_DEFINITIONS,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow switches."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    data_holder = entry_data["data_holder"]
    mqtt_client = entry_data["mqtt_client"]
    device_sn = entry.data[CONF_DEVICE_SN]

    switches = [
        EcoFlowSwitch(
            entry=entry,
            data_holder=data_holder,
            mqtt_client=mqtt_client,
            attr_key=attr_key,
            name=name,
            icon=icon,
            device_sn=device_sn,
        )
        for attr_key, name, icon in SWITCH_DEFINITIONS
    ]
    async_add_entities(switches)


class EcoFlowSwitch(SwitchEntity):
    """Represents a switchable output on the EcoFlow Delta Pro Ultra."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        data_holder,
        mqtt_client,
        attr_key: str,
        name: str,
        icon: str | None,
        device_sn: str,
    ) -> None:
        self._entry = entry
        self._data_holder = data_holder
        self._mqtt_client = mqtt_client
        self._attr_key = attr_key
        self._attr_name = name
        self._attr_icon = icon
        self._device_sn = device_sn
        self._attr_unique_id = f"{DOMAIN}_{device_sn}_{attr_key}"
        self._optimistic_state: bool | None = None

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
    def is_on(self) -> bool | None:
        if self._optimistic_state is not None:
            return self._optimistic_state
        return self._data_holder.get(self._attr_key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        success = await self.hass.async_add_executor_job(
            self._mqtt_client.set_param, self._attr_key, True
        )
        if success:
            self._optimistic_state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        success = await self.hass.async_add_executor_job(
            self._mqtt_client.set_param, self._attr_key, False
        )
        if success:
            self._optimistic_state = False
            self.async_write_ha_state()

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
        self._optimistic_state = None  # Revert to real data
        self.async_write_ha_state()
