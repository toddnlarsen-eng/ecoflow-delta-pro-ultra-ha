# EcoFlow Delta Pro Ultra — Home Assistant Integration

A custom component for Home Assistant that integrates the **EcoFlow Delta Pro Ultra** battery system via the official EcoFlow Open API (MQTT + REST).

---

## Features

| Category | Entities |
|---|---|
| **Sensors** | Battery SOC, Capacity, Voltage, Current, Temperature, Cycles, Remaining Time, AC/DC/USB/Solar/Grid power & voltage/current metrics |
| **Switches** | AC Output, DC Output, EPS (Emergency Power Supply) Mode |
| **Numbers (sliders)** | AC Charging Power Limit, Backup Reserve Level, Charge Upper Limit, Discharge Lower Limit |

---

## Prerequisites

1. An **EcoFlow Developer Account** — sign up at [developer.ecoflow.com](https://developer.ecoflow.com)
2. An **Access Key** and **Secret Key** from the EcoFlow Developer Portal
3. Your **device serial number (SN)** — found in the EcoFlow app under device settings

---

## Installation

### Via HACS (recommended)

1. In HACS, go to **Integrations → Custom Repositories**
2. Add `https://github.com/yourusername/ecoflow-delta-pro-ultra-ha` as an **Integration**
3. Install **EcoFlow Delta Pro Ultra**
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/ecoflow_delta_pro_ultra` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **EcoFlow Delta Pro Ultra**
3. Enter your **Access Key**, **Secret Key**, and **Device Serial Number**
4. Click **Submit**

The integration will validate your credentials, then start an MQTT connection to the EcoFlow cloud broker.

---

## Architecture

```
Home Assistant
    └── ConfigEntry
        ├── EcoFlowMQTTClient  (paho-mqtt, TLS, cloud push)
        │     ├── Subscribes: /app/device/property/get/{sn}
        │     └── Publishes:  /app/{uid}/device/property/set/{sn}
        ├── EcoFlowDataHolder  (in-memory state cache)
        └── Platforms
              ├── sensor.py    (25 read-only sensors)
              ├── switch.py    (3 on/off controls)
              └── number.py    (4 numeric sliders)
```

### Data flow

1. On connect, the client requests a full quota snapshot.
2. EcoFlow pushes real-time updates via MQTT whenever values change.
3. A periodic fallback poll (every 30 s) re-requests the full quota in case any push was missed.
4. All entities listen for the `ecoflow_delta_pro_ultra_update_<entry_id>` HA dispatcher signal and refresh their state.

---

## Entities Reference

### Sensors

| Entity | Unit | Notes |
|---|---|---|
| Battery Level | % | Main SoC display value |
| Battery Capacity | Wh | Full capacity |
| Battery Voltage | V | Min cell voltage |
| Battery Current | A | |
| Battery Temperature | °C | Max cell temp |
| Battery Cycles | — | Charge cycles |
| Battery Remain Time | min | Charge or discharge remaining |
| Total Input Power | W | Sum of all inputs |
| Total Output Power | W | Sum of all outputs |
| AC Input Power | W | Shore / grid charging |
| AC Input Voltage | V | |
| AC Input Frequency | Hz | |
| AC Output Power | W | Load on AC inverter |
| AC Output Voltage | V | |
| AC Charging Power | W | Current AC charge rate |
| DC Output Power | W | Car port / 12 V DC |
| USB Output Power | W | USB-A |
| USB-C Output Power | W | |
| Solar Input Power | W | MPPT combined |
| Solar Input Voltage | V | |
| Solar Input Current | A | |
| Grid Input Power | W | Grid-tied input |
| Backup Reserve Level | % | Minimum SoC held for backup |
| Charge Upper Limit | % | Max charge target |
| Discharge Lower Limit | % | Min discharge cutoff |

### Switches

| Entity | Description |
|---|---|
| AC Output | Enable / disable AC inverter output |
| DC Output | Enable / disable 12 V DC / car port |
| EPS Mode | Enable / disable Emergency Power Supply (UPS) mode |

### Numbers (sliders)

| Entity | Range | Step |
|---|---|---|
| AC Charging Power Limit | 200–3000 W | 100 W |
| Backup Reserve Level | 0–100 % | 1 % |
| Charge Upper Limit | 50–100 % | 1 % |
| Discharge Lower Limit | 0–30 % | 1 % |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| All sensors show "unavailable" | Check MQTT connectivity — port 8883 must be reachable outbound |
| `invalid_auth` during setup | Verify Access Key / Secret Key in EcoFlow Developer Portal |
| Values not updating | Check HA logs for MQTT disconnect messages; the 30 s poll should recover automatically |
| `paho-mqtt` not found | Restart HA after installation; the requirement is auto-installed |

---

## License

MIT
