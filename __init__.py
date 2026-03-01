"""EcoFlow Delta Pro Ultra integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_ACCESS_KEY,
    CONF_SECRET_KEY,
    CONF_DEVICE_SN,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .ecoflow_client import EcoFlowDataHolder, EcoFlowMQTTClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]
SIGNAL_UPDATE = f"{DOMAIN}_update"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoFlow Delta Pro Ultra from a config entry."""
    access_key = entry.data[CONF_ACCESS_KEY]
    secret_key = entry.data[CONF_SECRET_KEY]
    device_sn = entry.data[CONF_DEVICE_SN]
    user_id = entry.data.get("user_id", "")

    data_holder = EcoFlowDataHolder()

    def on_data_update(params: dict) -> None:
        data_holder.update(params)
        async_dispatcher_send(hass, f"{SIGNAL_UPDATE}_{entry.entry_id}")

    def on_connected() -> None:
        _LOGGER.info("EcoFlow MQTT connected for device %s", device_sn)

    def on_disconnected() -> None:
        _LOGGER.warning("EcoFlow MQTT disconnected for device %s", device_sn)

    mqtt_client = EcoFlowMQTTClient(
        access_key=access_key,
        secret_key=secret_key,
        device_sn=device_sn,
        user_id=user_id,
        on_data_update=on_data_update,
        on_connected=on_connected,
        on_disconnected=on_disconnected,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "mqtt_client": mqtt_client,
        "data_holder": data_holder,
    }

    # Connect in executor to avoid blocking event loop
    await hass.async_add_executor_job(mqtt_client.connect)

    # Periodic refresh fallback
    def _periodic_refresh(now=None) -> None:
        if mqtt_client.connected:
            mqtt_client.request_data()

    entry.async_on_unload(
        async_track_time_interval(
            hass,
            _periodic_refresh,
            timedelta(seconds=UPDATE_INTERVAL),
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(entry_data["mqtt_client"].disconnect)
    return unload_ok
