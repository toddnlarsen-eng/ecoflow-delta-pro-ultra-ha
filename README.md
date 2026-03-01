# EcoFlow Delta Pro Ultra — Home Assistant Integration

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/yourusername/ecoflow-delta-pro-ultra-ha)](https://github.com/yourusername/ecoflow-delta-pro-ultra-ha/releases)
[![HA Minimum Version](https://img.shields.io/badge/Home%20Assistant-2023.8%2B-blue)](https://www.home-assistant.io)
[![HACS Validation](https://github.com/yourusername/ecoflow-delta-pro-ultra-ha/actions/workflows/hacs.yml/badge.svg)](https://github.com/yourusername/ecoflow-delta-pro-ultra-ha/actions/workflows/hacs.yml)
[![Hassfest](https://github.com/yourusername/ecoflow-delta-pro-ultra-ha/actions/workflows/hassfest.yml/badge.svg)](https://github.com/yourusername/ecoflow-delta-pro-ultra-ha/actions/workflows/hassfest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Integrate your **EcoFlow Delta Pro Ultra** battery system into Home Assistant with real-time monitoring and full control — powered by the official [EcoFlow Open API](https://developer.ecoflow.com) via MQTT + REST.

---

## Installation

### Via HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=yourusername&repository=ecoflow-delta-pro-ultra-ha&category=integration)

1. Click the badge above, or in HACS go to **Integrations → ⋮ → Custom Repositories**
2. Add `https://github.com/yourusername/ecoflow-delta-pro-ultra-ha` as an **Integration**
3. Search for **EcoFlow Delta Pro Ultra** and install it
4. **Restart Home Assistant**

### Manual

1. Download the [latest release](https://github.com/yourusername/ecoflow-delta-pro-ultra-ha/releases/latest) zip
2. Extract `ecoflow_delta_pro_ultra` into your HA `config/custom_components/` directory
3. **Restart Home Assistant**

---

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ecoflow_delta_pro_ultra)

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **EcoFlow Delta Pro Ultra**
3. Enter your credentials:

| Field | Where to find it |
|---|---|
| **Access Key** | [EcoFlow Developer Portal](https://developer.ecoflow.com) → API Keys |
| **Secret Key** | [EcoFlow Developer Portal](https://developer.ecoflow.com) → API Keys |
| **Device SN** | EcoFlow app → Device → Settings → Device Info |

---

## Features

### 📊 Sensors (25)

| Entity | Unit | Device Class |
|---|---|---|
| Battery Level | % | battery |
| Battery Capacity | Wh | energy_storage |
| Battery Voltage | V | voltage |
| Battery Current | A | current |
| Battery Temperature | °C | temperature |
| Battery Cycles | — | — |
| Battery Remain Time | min | — |
| Total Input Power | W | power |
| Total Output Power | W | power |
| AC Input Power | W | power |
| AC Input Voltage | V | voltage |
| AC Input Frequency | Hz | frequency |
| AC Output Power | W | power |
| AC Output Voltage | V | voltage |
| AC Charging Power | W | power |
| DC Output Power | W | power |
| USB Output Power | W | power |
| USB-C Output Power | W | power |
| Solar Input Power | W | power |
| Solar Input Voltage | V | voltage |
| Solar Input Current | A | current |
| Grid Input Power | W | power |
| Backup Reserve Level | % | battery |
| Charge Upper Limit | % | battery |
| Discharge Lower Limit | % | battery |

### 🔌 Switches (3)

| Entity | Description |
|---|---|
| AC Output | Enable / disable the AC inverter output |
| DC Output | Enable / disable the 12 V car port |
| EPS Mode | Enable / disable Emergency Power Supply (UPS) mode |

### 🎚️ Number Sliders (4)

| Entity | Range | Step |
|---|---|---|
| AC Charging Power Limit | 200–3000 W | 100 W |
| Backup Reserve Level | 0–100 % | 1 % |
| Charge Upper Limit | 50–100 % | 1 % |
| Discharge Lower Limit | 0–30 % | 1 % |

---

## Architecture

```
Home Assistant
└── ConfigEntry
    ├── EcoFlowMQTTClient  (paho-mqtt, TLS 8883, cloud push)
    │     ├── Subscribe: /app/device/property/get/{sn}
    │     └── Publish:   /app/{uid}/device/property/set/{sn}
    ├── EcoFlowDataHolder  (in-memory state cache)
    └── Platforms
          ├── sensor.py    (25 read-only sensors)
          ├── switch.py    (3 on/off controls)
          └── number.py    (4 numeric sliders)
```

Data flows in real-time via MQTT push. A 30-second fallback poll re-requests the full quota in case any message is missed.

---

## Requirements

- Home Assistant **2023.8.0** or newer
- Outbound TCP to `mqtt.ecoflow.com:8883` (TLS)
- Outbound HTTPS to `api.ecoflow.com` (setup/validation only)
- Free [EcoFlow Developer Account](https://developer.ecoflow.com)

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| All sensors show "unavailable" | Ensure port 8883 outbound is not blocked by your firewall |
| `invalid_auth` during setup | Re-generate API keys in the EcoFlow Developer Portal |
| Values stuck / not updating | Check HA logs for MQTT disconnect; the 30 s poll recovers automatically |
| `paho-mqtt` missing | Fully restart HA after install — the requirement installs on first boot |

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.ecoflow_delta_pro_ultra: debug
```

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss significant changes.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes and open a PR against `main`

---

## License

[MIT](LICENSE)
