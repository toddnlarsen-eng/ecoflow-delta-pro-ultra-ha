"""Constants for EcoFlow Delta Pro Ultra integration."""

DOMAIN = "ecoflow_delta_pro_ultra"

# Config keys
CONF_ACCESS_KEY = "access_key"
CONF_SECRET_KEY = "secret_key"
CONF_DEVICE_SN = "device_sn"

# EcoFlow MQTT broker
ECOFLOW_MQTT_HOST = "mqtt.ecoflow.com"
ECOFLOW_MQTT_PORT = 8883
ECOFLOW_API_HOST = "https://api.ecoflow.com"

# Update interval (seconds) for polling fallback
UPDATE_INTERVAL = 30

# MQTT Topics
TOPIC_GET_QUOTA = "/app/device/property/{device_sn}"
TOPIC_SET = "/app/{user_id}/device/property/set/{device_sn}"
TOPIC_QUOTA_REPLY = "/app/device/property/get/{device_sn}"

# Battery
ATTR_BATTERY_SOC = "battery_soc"
ATTR_BATTERY_CAPACITY = "battery_capacity"
ATTR_BATTERY_VOLTAGE = "battery_voltage"
ATTR_BATTERY_CURRENT = "battery_current"
ATTR_BATTERY_TEMP = "battery_temp"
ATTR_BATTERY_CYCLES = "battery_cycles"
ATTR_BATTERY_REMAIN_TIME = "battery_remain_time"

# Power
ATTR_TOTAL_IN_POWER = "total_in_power"
ATTR_TOTAL_OUT_POWER = "total_out_power"

# AC
ATTR_AC_IN_POWER = "ac_in_power"
ATTR_AC_IN_VOLTAGE = "ac_in_voltage"
ATTR_AC_IN_FREQ = "ac_in_freq"
ATTR_AC_OUT_POWER = "ac_out_power"
ATTR_AC_OUT_ENABLED = "ac_out_enabled"
ATTR_AC_OUT_VOLTAGE = "ac_out_voltage"
ATTR_AC_CHARGE_POWER = "ac_charge_power"

# DC / USB
ATTR_DC_OUT_POWER = "dc_out_power"
ATTR_DC_OUT_ENABLED = "dc_out_enabled"
ATTR_USB_OUT_POWER = "usb_out_power"
ATTR_USB_C_OUT_POWER = "usb_c_out_power"

# Solar
ATTR_SOLAR_IN_POWER = "solar_in_power"
ATTR_SOLAR_IN_VOLTAGE = "solar_in_voltage"
ATTR_SOLAR_IN_CURRENT = "solar_in_current"

# Grid / EPS
ATTR_GRID_IN_POWER = "grid_in_power"
ATTR_EPS_ENABLED = "eps_enabled"
ATTR_BACKUP_RESERVE_SOC = "backup_reserve_soc"
ATTR_CHARGE_UPPER_LIMIT = "charge_upper_limit"
ATTR_DISCHARGE_LOWER_LIMIT = "discharge_lower_limit"

# System
ATTR_STATUS = "status"

# Dispatcher signal for state updates
SIGNAL_UPDATE = f"{DOMAIN}_update"

# Sensor definitions: (key, name, unit, device_class, state_class, icon)
SENSOR_DEFINITIONS = [
    (ATTR_BATTERY_SOC, "Battery Level", "%", "battery", "measurement", None),
    (ATTR_BATTERY_CAPACITY, "Battery Capacity", "Wh", "energy_storage", "measurement", "mdi:battery"),
    (ATTR_BATTERY_VOLTAGE, "Battery Voltage", "V", "voltage", "measurement", None),
    (ATTR_BATTERY_CURRENT, "Battery Current", "A", "current", "measurement", None),
    (ATTR_BATTERY_TEMP, "Battery Temperature", "°C", "temperature", "measurement", None),
    (ATTR_BATTERY_CYCLES, "Battery Cycles", None, None, "total_increasing", "mdi:battery-sync"),
    (ATTR_BATTERY_REMAIN_TIME, "Battery Remain Time", "min", None, "measurement", "mdi:timer"),
    (ATTR_TOTAL_IN_POWER, "Total Input Power", "W", "power", "measurement", None),
    (ATTR_TOTAL_OUT_POWER, "Total Output Power", "W", "power", "measurement", None),
    (ATTR_AC_IN_POWER, "AC Input Power", "W", "power", "measurement", None),
    (ATTR_AC_IN_VOLTAGE, "AC Input Voltage", "V", "voltage", "measurement", None),
    (ATTR_AC_IN_FREQ, "AC Input Frequency", "Hz", "frequency", "measurement", None),
    (ATTR_AC_OUT_POWER, "AC Output Power", "W", "power", "measurement", None),
    (ATTR_AC_OUT_VOLTAGE, "AC Output Voltage", "V", "voltage", "measurement", None),
    (ATTR_AC_CHARGE_POWER, "AC Charging Power", "W", "power", "measurement", None),
    (ATTR_DC_OUT_POWER, "DC Output Power", "W", "power", "measurement", None),
    (ATTR_USB_OUT_POWER, "USB Output Power", "W", "power", "measurement", None),
    (ATTR_USB_C_OUT_POWER, "USB-C Output Power", "W", "power", "measurement", None),
    (ATTR_SOLAR_IN_POWER, "Solar Input Power", "W", "power", "measurement", None),
    (ATTR_SOLAR_IN_VOLTAGE, "Solar Input Voltage", "V", "voltage", "measurement", None),
    (ATTR_SOLAR_IN_CURRENT, "Solar Input Current", "A", "current", "measurement", None),
    (ATTR_GRID_IN_POWER, "Grid Input Power", "W", "power", "measurement", None),
    (ATTR_BACKUP_RESERVE_SOC, "Backup Reserve Level", "%", "battery", "measurement", "mdi:battery-lock"),
    (ATTR_CHARGE_UPPER_LIMIT, "Charge Upper Limit", "%", "battery", "measurement", "mdi:battery-arrow-up"),
    (ATTR_DISCHARGE_LOWER_LIMIT, "Discharge Lower Limit", "%", "battery", "measurement", "mdi:battery-arrow-down"),
]

# Switch definitions: (key, name, icon)
SWITCH_DEFINITIONS = [
    (ATTR_AC_OUT_ENABLED, "AC Output", "mdi:power-plug"),
    (ATTR_DC_OUT_ENABLED, "DC Output", "mdi:car-battery"),
    (ATTR_EPS_ENABLED, "EPS Mode", "mdi:shield-lightning"),
]

# Number definitions: (key, name, unit, min, max, step, icon, mode)
NUMBER_DEFINITIONS = [
    (ATTR_AC_CHARGE_POWER, "AC Charging Power Limit", "W", 200, 3000, 100, "mdi:lightning-bolt", "slider"),
    (ATTR_BACKUP_RESERVE_SOC, "Backup Reserve Level", "%", 0, 100, 1, "mdi:battery-lock", "slider"),
    (ATTR_CHARGE_UPPER_LIMIT, "Charge Upper Limit", "%", 50, 100, 1, "mdi:battery-arrow-up", "slider"),
    (ATTR_DISCHARGE_LOWER_LIMIT, "Discharge Lower Limit", "%", 0, 30, 1, "mdi:battery-arrow-down", "slider"),
]
