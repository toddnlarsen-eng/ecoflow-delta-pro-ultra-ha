"""Config flow for EcoFlow Delta Pro Ultra integration."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import random
import string
import time
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ACCESS_KEY,
    CONF_SECRET_KEY,
    CONF_DEVICE_SN,
    DOMAIN,
    ECOFLOW_API_HOST,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_KEY): str,
        vol.Required(CONF_SECRET_KEY): str,
        vol.Required(CONF_DEVICE_SN): str,
    }
)


def _generate_nonce(length: int = 16) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


async def _validate_credentials(
    hass: HomeAssistant, access_key: str, secret_key: str, device_sn: str
) -> dict[str, Any]:
    """Validate credentials against EcoFlow REST API and get device info."""
    nonce = _generate_nonce()
    timestamp = str(int(time.time() * 1000))

    params = {
        "accessKey": access_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "sn": device_sn,
    }
    sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sign = hmac.new(
        secret_key.encode("utf-8"),
        sorted_params.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "accessKey": access_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign,
        "Content-Type": "application/json;charset=UTF-8",
    }

    session = async_get_clientsession(hass)
    url = f"{ECOFLOW_API_HOST}/iot-open/sign/device/quota/all"
    async with session.get(url, headers=headers, params={"sn": device_sn}) as resp:
        if resp.status == 401:
            raise ValueError("invalid_auth")
        resp.raise_for_status()
        data = await resp.json()

    if data.get("code") != "0":
        msg = data.get("message", "unknown_error")
        raise ValueError(msg)

    # Extract userId from token info endpoint
    url_user = f"{ECOFLOW_API_HOST}/iot-open/sign/certification"
    async with session.get(url_user, headers=headers) as resp:
        resp.raise_for_status()
        user_data = await resp.json()

    user_id = user_data.get("data", {}).get("userId", "")
    return {"user_id": user_id}


class EcoFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for EcoFlow Delta Pro Ultra."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            access_key = user_input[CONF_ACCESS_KEY].strip()
            secret_key = user_input[CONF_SECRET_KEY].strip()
            device_sn = user_input[CONF_DEVICE_SN].strip()

            await self.async_set_unique_id(device_sn)
            self._abort_if_unique_id_configured()

            try:
                extra = await _validate_credentials(
                    self.hass, access_key, secret_key, device_sn
                )
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except ValueError as err:
                errors["base"] = str(err) if str(err) in ("invalid_auth",) else "unknown"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during config flow validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Delta Pro Ultra ({device_sn})",
                    data={
                        CONF_ACCESS_KEY: access_key,
                        CONF_SECRET_KEY: secret_key,
                        CONF_DEVICE_SN: device_sn,
                        "user_id": extra.get("user_id", ""),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_docs": "https://developer.ecoflow.com/us/document/generalInfo"
            },
        )
