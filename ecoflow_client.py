"""EcoFlow API client for Delta Pro Ultra."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import random
import string
import time
from typing import Any, Callable, Optional
import urllib.parse

import paho.mqtt.client as mqtt

from .const import (
    ECOFLOW_MQTT_HOST,
    ECOFLOW_MQTT_PORT,
    TOPIC_GET_QUOTA,
    TOPIC_QUOTA_REPLY,
    TOPIC_SET,
    ATTR_BATTERY_SOC,
    ATTR_BATTERY_CAPACITY,
    ATTR_BATTERY_VOLTAGE,
    ATTR_BATTERY_CURRENT,
    ATTR_BATTERY_TEMP,
    ATTR_BATTERY_CYCLES,
    ATTR_BATTERY_REMAIN_TIME,
    ATTR_TOTAL_IN_POWER,
    ATTR_TOTAL_OUT_POWER,
    ATTR_AC_IN_POWER,
    ATTR_AC_IN_VOLTAGE,
    ATTR_AC_IN_FREQ,
    ATTR_AC_OUT_POWER,
    ATTR_AC_OUT_ENABLED,
    ATTR_AC_OUT_VOLTAGE,
    ATTR_AC_CHARGE_POWER,
    ATTR_DC_OUT_POWER,
    ATTR_DC_OUT_ENABLED,
    ATTR_USB_OUT_POWER,
    ATTR_USB_C_OUT_POWER,
    ATTR_SOLAR_IN_POWER,
    ATTR_SOLAR_IN_VOLTAGE,
    ATTR_SOLAR_IN_CURRENT,
    ATTR_GRID_IN_POWER,
    ATTR_EPS_ENABLED,
    ATTR_BACKUP_RESERVE_SOC,
    ATTR_CHARGE_UPPER_LIMIT,
    ATTR_DISCHARGE_LOWER_LIMIT,
)

_LOGGER = logging.getLogger(__name__)

# Maps EcoFlow raw MQTT parameter keys to our internal attribute names
# Based on EcoFlow Open API documentation for Delta Pro Ultra (BP5000)
PARAM_MAP: dict[str, str] = {
    # Battery / BMS
    "bms_bmsStatus.minCellSoc":        ATTR_BATTERY_SOC,
    "bms_bmsStatus.maxCellTemp":       ATTR_BATTERY_TEMP,
    "bms_bmsStatus.fullCap":           ATTR_BATTERY_CAPACITY,
    "bms_bmsStatus.minCellVol":        ATTR_BATTERY_VOLTAGE,
    "bms_bmsStatus.amp":               ATTR_BATTERY_CURRENT,
    "bms_bmsStatus.cycles":            ATTR_BATTERY_CYCLES,
    # EMS
    "ems.chgRemainTime":               ATTR_BATTERY_REMAIN_TIME,
    "ems.dsgRemainTime":               ATTR_BATTERY_REMAIN_TIME,
    "ems.lcdShowSoc":                  ATTR_BATTERY_SOC,
    "ems.minOpenOilEbSoc":             ATTR_DISCHARGE_LOWER_LIMIT,
    "ems.maxChargeSoc":                ATTR_CHARGE_UPPER_LIMIT,
    "ems.bpPowerSoc":                  ATTR_BACKUP_RESERVE_SOC,
    # Inverter
    "inv.inputWatts":                  ATTR_AC_IN_POWER,
    "inv.outputWatts":                 ATTR_AC_OUT_POWER,
    "inv.acInVol":                     ATTR_AC_IN_VOLTAGE,
    "inv.invOutVol":                   ATTR_AC_OUT_VOLTAGE,
    "inv.acInFreq":                    ATTR_AC_IN_FREQ,
    "inv.cfgAcWatts":                  ATTR_AC_CHARGE_POWER,
    "inv.acDipSwitch":                 ATTR_AC_OUT_ENABLED,
    "inv.eps":                         ATTR_EPS_ENABLED,
    # Power management
    "pd.wattsInSum":                   ATTR_TOTAL_IN_POWER,
    "pd.wattsOutSum":                  ATTR_TOTAL_OUT_POWER,
    "pd.dcOutState":                   ATTR_DC_OUT_ENABLED,
    "pd.carWatts":                     ATTR_DC_OUT_POWER,
    "pd.usb1Watts":                    ATTR_USB_OUT_POWER,
    "pd.typecWatts":                   ATTR_USB_C_OUT_POWER,
    # MPPT / Solar
    "mppt.inVol":                      ATTR_SOLAR_IN_VOLTAGE,
    "mppt.inAmp":                      ATTR_SOLAR_IN_CURRENT,
    "mppt.inWatts":                    ATTR_SOLAR_IN_POWER,
    # Grid
    "grid.inWatts":                    ATTR_GRID_IN_POWER,
}

# Maps our attribute names to the EcoFlow MQTT set command params
SET_PARAM_MAP: dict[str, dict] = {
    ATTR_AC_OUT_ENABLED:      {"moduleType": 0, "operateType": "acOutCfg",   "params": {"enabled": None}},
    ATTR_DC_OUT_ENABLED:      {"moduleType": 0, "operateType": "dcOutCfg",   "params": {"enabled": None}},
    ATTR_EPS_ENABLED:         {"moduleType": 0, "operateType": "epsCfg",     "params": {"enabled": None}},
    ATTR_AC_CHARGE_POWER:     {"moduleType": 0, "operateType": "acChgCfg",   "params": {"chgWatts": None, "chgPauseFlag": 0}},
    ATTR_BACKUP_RESERVE_SOC:  {"moduleType": 0, "operateType": "bpPowerSoc", "params": {"backupForceAh": None}},
    ATTR_CHARGE_UPPER_LIMIT:  {"moduleType": 0, "operateType": "upsConfig",  "params": {"maxChargeSoc": None}},
    ATTR_DISCHARGE_LOWER_LIMIT: {"moduleType": 0, "operateType": "dsgCfg",   "params": {"minDsgSoc": None}},
}

_VALUE_KEY_MAP: dict[str, str] = {
    ATTR_AC_OUT_ENABLED:        "enabled",
    ATTR_DC_OUT_ENABLED:        "enabled",
    ATTR_EPS_ENABLED:           "enabled",
    ATTR_AC_CHARGE_POWER:       "chgWatts",
    ATTR_BACKUP_RESERVE_SOC:    "backupForceAh",
    ATTR_CHARGE_UPPER_LIMIT:    "maxChargeSoc",
    ATTR_DISCHARGE_LOWER_LIMIT: "minDsgSoc",
}


def _generate_nonce(length: int = 16) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _sign(secret_key: str, params: dict) -> str:
    """Generate HMAC-SHA256 signature for EcoFlow API."""
    sorted_params = "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )
    return hmac.new(
        secret_key.encode("utf-8"),
        sorted_params.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class EcoFlowApiError(Exception):
    """Raised when the EcoFlow API returns an error."""


class EcoFlowDataHolder:
    """Holds current state data for the device."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def update(self, raw: dict[str, Any]) -> None:
        """Update from raw MQTT payload params."""
        for raw_key, mapped_key in PARAM_MAP.items():
            # Support both flat and nested param structures
            if raw_key in raw:
                value = raw[raw_key]
                # Normalize boolean-ish integers
                if mapped_key in (ATTR_AC_OUT_ENABLED, ATTR_DC_OUT_ENABLED, ATTR_EPS_ENABLED):
                    value = bool(value)
                self.data[mapped_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class EcoFlowMQTTClient:
    """Manages MQTT connection to EcoFlow cloud broker."""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        device_sn: str,
        user_id: str,
        on_data_update: Callable[[dict], None],
        on_connected: Optional[Callable[[], None]] = None,
        on_disconnected: Optional[Callable[[], None]] = None,
    ) -> None:
        self._access_key = access_key
        self._secret_key = secret_key
        self._device_sn = device_sn
        self._user_id = user_id
        self._on_data_update = on_data_update
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._client: Optional[mqtt.Client] = None
        self._connected = False

        self._topic_quota_reply = TOPIC_QUOTA_REPLY.format(device_sn=device_sn)
        self._topic_set = TOPIC_SET.format(user_id=user_id, device_sn=device_sn)
        self._topic_get = TOPIC_GET_QUOTA.format(device_sn=device_sn)

    @property
    def connected(self) -> bool:
        return self._connected

    def _build_auth(self) -> dict[str, str]:
        nonce = _generate_nonce()
        timestamp = str(int(time.time() * 1000))
        params = {
            "accessKey": self._access_key,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        sign = _sign(self._secret_key, params)
        return {
            "accessKey": self._access_key,
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": sign,
        }

    def connect(self) -> None:
        """Establish MQTT connection."""
        auth = self._build_auth()
        client_id = f"ANDROID_{_generate_nonce(8)}_{self._user_id}"

        self._client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        self._client.username_pw_set(
            username=auth["accessKey"],
            password=json.dumps({
                "sign": auth["sign"],
                "nonce": auth["nonce"],
                "timestamp": auth["timestamp"],
            }),
        )
        self._client.tls_set()  # Use default TLS context (CA bundle)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        _LOGGER.debug("Connecting to EcoFlow MQTT broker at %s:%s", ECOFLOW_MQTT_HOST, ECOFLOW_MQTT_PORT)
        self._client.connect_async(ECOFLOW_MQTT_HOST, ECOFLOW_MQTT_PORT, keepalive=60)
        self._client.loop_start()

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            _LOGGER.info("Connected to EcoFlow MQTT broker")
            self._connected = True
            client.subscribe(self._topic_quota_reply)
            _LOGGER.debug("Subscribed to %s", self._topic_quota_reply)
            # Request full quota immediately
            self.request_data()
            if self._on_connected:
                self._on_connected()
        else:
            _LOGGER.error("MQTT connection failed with result code %s", rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected = False
        _LOGGER.warning("Disconnected from EcoFlow MQTT (rc=%s)", rc)
        if self._on_disconnected:
            self._on_disconnected()

    def _on_message(self, client, userdata, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            _LOGGER.debug("MQTT message on %s: %s", msg.topic, payload)
            params = payload.get("params", {})
            if params:
                self._on_data_update(params)
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            _LOGGER.warning("Failed to decode MQTT message: %s", err)

    def request_data(self) -> None:
        """Request all quota data from the device."""
        if not self._client or not self._connected:
            return
        payload = json.dumps({"sn": self._device_sn})
        self._client.publish(self._topic_get, payload)
        _LOGGER.debug("Requested quota data for %s", self._device_sn)

    def set_param(self, attribute: str, value: Any) -> bool:
        """Send a set command to the device."""
        if not self._client or not self._connected:
            _LOGGER.error("Cannot set param: MQTT not connected")
            return False

        template = SET_PARAM_MAP.get(attribute)
        if not template:
            _LOGGER.error("No set command defined for attribute: %s", attribute)
            return False

        import copy
        command = copy.deepcopy(template)
        value_key = _VALUE_KEY_MAP.get(attribute)
        if value_key:
            command["params"][value_key] = int(value) if not isinstance(value, bool) else int(value)

        payload = json.dumps({
            "id": int(time.time()),
            "version": "1.0",
            "sn": self._device_sn,
            **command,
        })
        result = self._client.publish(self._topic_set, payload)
        _LOGGER.debug("Set %s=%s (mid=%s)", attribute, value, result.mid)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
