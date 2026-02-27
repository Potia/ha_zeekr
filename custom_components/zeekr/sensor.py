# custom_components/zeekr/sensor.py
"""Sensor platform for Zeekr integration"""

import logging
from typing import Any, Dict
from datetime import datetime

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfPressure,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ICON_BATTERY, ICON_TEMPERATURE, ICON_CAR
from .coordinator import ZeekrDataCoordinator
from .vehicle_parser import VehicleDataParser

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigType,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zeekr sensors"""

    coordinator: ZeekrDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # Для каждого автомобиля создаем датчики
    for vin in coordinator.data.keys():
        entities.extend([
            # ========== ОСНОВНЫЕ ДАТЧИКИ ==========
            ZeekrBatterySensor(coordinator, vin),
            ZeekrAuxBatteryPercentageSensor(coordinator, vin),
            ZeekrAuxBatteryVoltageSensor(coordinator, vin),
            ZeekrDistanceToEmptySensor(coordinator, vin),
            ZeekrInteriorTempSensor(coordinator, vin),
            ZeekrExteriorTempSensor(coordinator, vin),
            ZeekrOdometerSensor(coordinator, vin),
            ZeekrCurrentSpeedSensor(coordinator, vin),
            ZeekrAverageSpeedSensor(coordinator, vin),
            ZeekrDaysToServiceSensor(coordinator, vin),
            ZeekrDistanceToServiceSensor(coordinator, vin),
            ZeekrTirePressureDriverSensor(coordinator, vin),
            ZeekrTirePressurePassengerSensor(coordinator, vin),
            ZeekrTirePressureDriverRearSensor(coordinator, vin),
            ZeekrTirePressurePassengerRearSensor(coordinator, vin),
            ZeekrInteriorPM25Sensor(coordinator, vin),
            ZeekrParkTimeSensor(coordinator, vin),
            ZeekrLastUpdateTimeSensor(coordinator, vin),

            # ========== РАСШИРЕННЫЕ ДАТЧИКИ ==========
            # 🔋 Батарея (расширено)
            ZeekrStateOfChargeSensor(coordinator, vin),
            ZeekrStateOfHealthSensor(coordinator, vin),
            ZeekrBatteryExtendedVoltageSensor(coordinator, vin),
            ZeekrHVTempLevelSensor(coordinator, vin),
            ZeekrTimeToFullChargeSensor(coordinator, vin),

            # 🌡️ Температура шин
            ZeekrTireTempDriverSensor(coordinator, vin),
            ZeekrTireTempPassengerSensor(coordinator, vin),
            ZeekrTireTempDriverRearSensor(coordinator, vin),
            ZeekrTireTempPassengerRearSensor(coordinator, vin),

            # 🚙 Движение
            ZeekrTripMeter1Sensor(coordinator, vin),
            ZeekrTripMeter2Sensor(coordinator, vin),

            # 🔧 Обслуживание
            ZeekrEngineHoursToServiceSensor(coordinator, vin),
            ZeekrBrakeFluidLevelSensor(coordinator, vin),
            ZeekrWasherFluidLevelSensor(coordinator, vin),
            ZeekrEngineCoolantLevelSensor(coordinator, vin),

            # 💨 Воздух
            ZeekrExteriorPM25LevelSensor(coordinator, vin),
            ZeekrRelativeHumiditySensor(coordinator, vin),

            # 🅿️ Парковка
            ZeekrParkDurationSensor(coordinator, vin),

            # 🎯 Климат
            ZeekrSteeringWheelHeatingStatusSensor(coordinator, vin),
            ZeekrDriverHeatingStatusSensor(coordinator, vin),
            ZeekrPassengerHeatingStatusSensor(coordinator, vin),

            # 📍 Координаты
            ZeekrLatitudeSensor(coordinator, vin),
            ZeekrLongitudeSensor(coordinator, vin),
            ZeekrAltitudeSensor(coordinator, vin),

            # 🔐 Информация
            ZeekrPropulsionTypeSensor(coordinator, vin),

            # ⚡ Зарядка
            ZeekrChargePileVoltageSensor(coordinator, vin),
            ZeekrCurrentPowerInputSensor(coordinator, vin),
            ZeekrDCChargeCurrentSensor(coordinator, vin),
            ZeekrChargeStatusSensor(coordinator, vin),
        ])

    async_add_entities(entities)
    _LOGGER.info(f"✅ Added {len(entities)} sensors total for {len(coordinator.data)} vehicles")

# ==================== БАЗОВЫЙ КЛАСС ====================

class ZeekrBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Zeekr sensors"""

    def __init__(self, coordinator: ZeekrDataCoordinator, vin: str):
        """Initialize sensor"""
        super().__init__(coordinator)
        self.vin = vin
        self._attr_has_entity_name = True

        # Уникальный ID для каждого датчика
        self._attr_unique_id = f"{DOMAIN}_{vin}_{self._get_sensor_type()}"

        # Информация об устройстве
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": f"Zeekr {vin}",
            "manufacturer": "Zeekr",
            "model": "EV",
        }

    def _get_sensor_type(self) -> str:
        """Override in subclasses"""
        return "sensor"

    def _get_parser(self) -> VehicleDataParser:
        """Get parser for current vehicle data"""
        if self.vin not in self.coordinator.data:
            return None
        return VehicleDataParser(self.coordinator.data[self.vin])

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator"""
        self.async_write_ha_state()


# ==================== ОСНОВНЫЕ ДАТЧИКИ ====================

class ZeekrBatterySensor(ZeekrBaseSensor):
    """Battery charge level sensor - основная батарея EV"""

    _attr_name = "Battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = ICON_BATTERY
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "battery"

    @property
    def native_value(self) -> int:
        """Return battery percentage"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return battery['battery_percentage']  # 71%
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return {
                "charge_status": battery['charge_status'],
                "distance_to_empty": f"{battery['distance_to_empty']} км",
                "avg_power_consumption": f"{battery['avg_power_consumption']} кВт",
            }
        return {}

class ZeekrAuxBatteryPercentageSensor(ZeekrBaseSensor):
    """12V auxiliary battery percentage"""

    _attr_name = "12V Battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery-12v"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "battery_12v_percentage"

    @property
    def native_value(self) -> float:
        """Return 12V battery percentage"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return round(battery['aux_battery_percentage'], 1)  # 98.4%
        return None


class ZeekrAuxBatteryVoltageSensor(ZeekrBaseSensor):
    """12V auxiliary battery voltage"""

    _attr_name = "12V Battery Voltage"
    _attr_native_unit_of_measurement = "V"
    _attr_icon = "mdi:battery-12v"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "battery_12v_voltage"

    @property
    def native_value(self) -> float:
        """Return 12V battery voltage"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return round(battery['aux_battery_voltage'], 3)  # 12.225V
        return None


class ZeekrDistanceToEmptySensor(ZeekrBaseSensor):
    """Distance to empty sensor"""

    _attr_name = "Distance to Empty"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:road-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "distance_to_empty"

    @property
    def native_value(self) -> int:
        """Return distance to empty"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return battery['distance_to_empty']
        return None


class ZeekrInteriorTempSensor(ZeekrBaseSensor):
    """Interior temperature sensor"""

    _attr_name = "Interior Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = ICON_TEMPERATURE
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "interior_temp"

    @property
    def native_value(self) -> float:
        """Return interior temperature"""
        parser = self._get_parser()
        if parser:
            temp = parser.get_temperature_info()
            return temp['interior_temp']
        return None


class ZeekrExteriorTempSensor(ZeekrBaseSensor):
    """Exterior temperature sensor"""

    _attr_name = "Exterior Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = ICON_TEMPERATURE
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "exterior_temp"

    @property
    def native_value(self) -> float:
        """Return exterior temperature"""
        parser = self._get_parser()
        if parser:
            temp = parser.get_temperature_info()
            return temp['exterior_temp']
        return None


class ZeekrOdometerSensor(ZeekrBaseSensor):
    """Odometer sensor"""

    _attr_name = "Odometer"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = ICON_CAR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def _get_sensor_type(self) -> str:
        return "odometer"

    @property
    def native_value(self) -> float:
        """Return odometer value"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return int(maintenance['odometer'])
        return None


class ZeekrCurrentSpeedSensor(ZeekrBaseSensor):
    """Current speed sensor"""

    _attr_name = "Current Speed"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_icon = "mdi:speedometer"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "current_speed"

    @property
    def native_value(self) -> float:
        """Return current speed"""
        parser = self._get_parser()
        if parser:
            movement = parser.get_movement_info()
            return movement['speed']
        return None


class ZeekrAverageSpeedSensor(ZeekrBaseSensor):
    """Average speed sensor"""

    _attr_name = "Average Speed"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_icon = "mdi:speedometer"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "average_speed"

    @property
    def native_value(self) -> int:
        """Return average speed"""
        parser = self._get_parser()
        if parser:
            movement = parser.get_movement_info()
            return movement['avg_speed']
        return None


class ZeekrDaysToServiceSensor(ZeekrBaseSensor):
    """Days to service sensor"""

    _attr_name = "Days to Service"
    _attr_icon = "mdi:calendar-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "days_to_service"

    @property
    def native_value(self) -> int:
        """Return days to service"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return maintenance['days_to_service']
        return None


class ZeekrDistanceToServiceSensor(ZeekrBaseSensor):
    """Distance to service sensor"""

    _attr_name = "Distance to Service"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:road-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "distance_to_service"

    @property
    def native_value(self) -> int:
        """Return distance to service"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return maintenance['distance_to_service']
        return None


class ZeekrTirePressureDriverSensor(ZeekrBaseSensor):
    """Tire pressure - driver front"""

    _attr_name = "Tire Pressure - Driver Front"
    _attr_native_unit_of_measurement = UnitOfPressure.KPA
    _attr_icon = "mdi:tire"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_pressure_driver"

    @property
    def native_value(self) -> float:
        """Return tire pressure"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['driver_tire'], 1)
        return None


class ZeekrTirePressurePassengerSensor(ZeekrBaseSensor):
    """Tire pressure - passenger front"""

    _attr_name = "Tire Pressure - Passenger Front"
    _attr_native_unit_of_measurement = UnitOfPressure.KPA
    _attr_icon = "mdi:tire"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_pressure_passenger"

    @property
    def native_value(self) -> float:
        """Return tire pressure"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['passenger_tire'], 1)
        return None


class ZeekrTirePressureDriverRearSensor(ZeekrBaseSensor):
    """Tire pressure - driver rear"""

    _attr_name = "Tire Pressure - Driver Rear"
    _attr_native_unit_of_measurement = UnitOfPressure.KPA
    _attr_icon = "mdi:tire"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_pressure_driver_rear"

    @property
    def native_value(self) -> float:
        """Return tire pressure"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['driver_rear_tire'], 1)
        return None


class ZeekrTirePressurePassengerRearSensor(ZeekrBaseSensor):
    """Tire pressure - passenger rear"""

    _attr_name = "Tire Pressure - Passenger Rear"
    _attr_native_unit_of_measurement = UnitOfPressure.KPA
    _attr_icon = "mdi:tire"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_pressure_passenger_rear"

    @property
    def native_value(self) -> float:
        """Return tire pressure"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['passenger_rear_tire'], 1)
        return None


class ZeekrInteriorPM25Sensor(ZeekrBaseSensor):
    """Interior PM2.5 sensor"""

    _attr_name = "Interior PM2.5"
    _attr_native_unit_of_measurement = "μg/m³"
    _attr_icon = "mdi:air-filter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "interior_pm25"

    @property
    def native_value(self) -> int:
        """Return PM2.5 level"""
        parser = self._get_parser()
        if parser:
            pollution = parser.get_pollution_info()
            return pollution['interior_pm25']
        return None


class ZeekrParkTimeSensor(ZeekrBaseSensor):
    """Park time sensor"""

    _attr_name = "Park Time"
    _attr_icon = "mdi:clock"

    def _get_sensor_type(self) -> str:
        return "park_time"

    @property
    def native_value(self) -> str:
        """Return park time as formatted text"""
        parser = self._get_parser()
        if parser:
            park_time_ms = int(parser.data.get('parkTime', {}).get('status', 0))

            if park_time_ms == 0:
                return "Не припаркован"

            park_datetime = datetime.fromtimestamp(park_time_ms / 1000)
            current_time = datetime.now()
            park_duration = current_time - park_datetime

            total_seconds = int(park_duration.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            if days > 0:
                return f"{days}д {hours}ч {minutes}м припаркован"
            elif hours > 0:
                return f"{hours}ч {minutes}м припаркован"
            else:
                return f"{minutes}м припаркован"

        return "N/A"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes"""
        parser = self._get_parser()
        if parser:
            park_time_ms = int(parser.data.get('parkTime', {}).get('status', 0))

            if park_time_ms > 0:
                park_datetime = datetime.fromtimestamp(park_time_ms / 1000)
                return {
                    "parked_since": park_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                }
        return {}


class ZeekrLastUpdateTimeSensor(ZeekrBaseSensor):
    """Last update time sensor - when vehicle last connected to server"""

    _attr_name = "Last Update Time"
    _attr_icon = "mdi:cloud-upload"

    def _get_sensor_type(self) -> str:
        return "last_update_time"

    @property
    def native_value(self) -> str:
        """Return last update time as formatted string"""
        parser = self._get_parser()
        if parser:
            timestamp = int(parser.data.get('updateTime', 0))
            if timestamp:
                update_datetime = datetime.fromtimestamp(timestamp / 1000)
                return update_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return "N/A"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes"""
        parser = self._get_parser()
        if parser:
            timestamp = int(parser.data.get('updateTime', 0))
            if timestamp:
                update_datetime = datetime.fromtimestamp(timestamp / 1000)
                current_time = datetime.now()
                time_diff = current_time - update_datetime

                total_seconds = int(time_diff.total_seconds())
                minutes = total_seconds // 60
                hours = minutes // 60
                days = hours // 24

                if days > 0:
                    time_ago = f"{days} дней назад"
                elif hours > 0:
                    time_ago = f"{hours} часов назад"
                elif minutes > 0:
                    time_ago = f"{minutes} минут назад"
                else:
                    time_ago = "только что"

                return {
                    "time_ago": time_ago,
                    "timestamp": timestamp,
                }
        return {}


# ==================== РАСШИРЕННЫЕ ДАТЧИКИ ====================
# 🔋 БАТАРЕЯ (РАСШИРЕНО)

class ZeekrStateOfChargeSensor(ZeekrBaseSensor):
    """State of Charge - какой-то внутренний параметр батереи"""

    _attr_name = "State of Charge"
    _attr_icon = "mdi:battery-heart"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "state_of_charge"

    @property
    def native_value(self) -> float:
        """Вернуть SOC"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return battery['soc']
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Дополнительная информация"""
        return {
            "note": "Внутренний параметр батареи (не процент)"
        }


class ZeekrStateOfHealthSensor(ZeekrBaseSensor):
    """State of Health - какой-то внутренний параметр батереи"""

    _attr_name = "State of Health"
    _attr_icon = "mdi:battery-check"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "state_of_health"

    @property
    def native_value(self) -> float:
        """Вернуть SOH"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return battery['soh']
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Дополнительная информация"""
        return {
            "note": "Внутренний параметр батереи (не процент здоровья)"
        }


class ZeekrBatteryExtendedVoltageSensor(ZeekrBaseSensor):
    """Напряжение батареи (расширено)"""

    _attr_name = "Battery Voltage Extended"
    _attr_native_unit_of_measurement = "V"
    _attr_icon = "mdi:lightning-bolt"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "battery_voltage_extended"

    @property
    def native_value(self) -> float:
        """Вернуть напряжение 12V батареи"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return round(battery['aux_battery_voltage'], 2)  # ✅ 12.225V
        return None


class ZeekrHVTempLevelSensor(ZeekrBaseSensor):
    """Уровень HV температуры батареи"""

    _attr_name = "HV Temperature Level"
    _attr_icon = "mdi:thermometer-alert"
    # ❌ УДАЛЯЕМ: _attr_state_class = SensorStateClass.MEASUREMENT
    # ❌ УДАЛЯЕМ: _attr_device_class = ...
    # Оставляем только text!

    def _get_sensor_type(self) -> str:
        return "hv_temp_level"

    @property
    def native_value(self) -> str:
        """Вернуть уровень температуры (текст)"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return battery['hv_temp_level']  # "Немного холодная ❄️"
        return "Неизвестно"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Дополнительная информация"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return {
                "numeric_value": battery['hv_temp_level_numeric'],
                "description": "1=теплая 🔥, 2=немного холодная ❄️, 3=холодная 🥶, 4=сильно холодная 🧊"
            }
        return {}


class ZeekrTimeToFullChargeSensor(ZeekrBaseSensor):
    """Время до полной зарядки"""

    _attr_name = "Time to Full Charge"
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:battery-charging"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "time_to_full_charge"

    @property
    def native_value(self) -> int:
        """Вернуть время зарядки"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            value = battery['time_to_fully_charged']
            # Если значение 2047 или больше, это означает "неопределено"
            return None if value >= 2047 else value
        return None


# ==================== 🌡️ ТЕМПЕРАТУРА ШИН ====================

class ZeekrTireTempDriverSensor(ZeekrBaseSensor):
    """Температура передней левой шины"""

    _attr_name = "Tire Temp - Driver Front"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-lines"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_temp_driver_front"

    @property
    def native_value(self) -> float:
        """Вернуть температуру"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['driver_temp'], 1)
        return None


class ZeekrTireTempPassengerSensor(ZeekrBaseSensor):
    """Температура передней правой шины"""

    _attr_name = "Tire Temp - Passenger Front"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-lines"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_temp_passenger_front"

    @property
    def native_value(self) -> float:
        """Вернуть температуру"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['passenger_temp'], 1)
        return None


class ZeekrTireTempDriverRearSensor(ZeekrBaseSensor):
    """Температура задней левой шины"""

    _attr_name = "Tire Temp - Driver Rear"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-lines"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_temp_driver_rear"

    @property
    def native_value(self) -> float:
        """Вернуть температуру"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['driver_rear_temp'], 1)
        return None


class ZeekrTireTempPassengerRearSensor(ZeekrBaseSensor):
    """Температура задней правой шины"""

    _attr_name = "Tire Temp - Passenger Rear"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_icon = "mdi:thermometer-lines"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "tire_temp_passenger_rear"

    @property
    def native_value(self) -> float:
        """Вернуть температуру"""
        parser = self._get_parser()
        if parser:
            tires = parser.get_tires_info()
            return round(tires['passenger_rear_temp'], 1)
        return None


# ==================== 🚙 ДВИЖЕНИЕ (РАСШИРЕНО) ====================

class ZeekrTripMeter1Sensor(ZeekrBaseSensor):
    """Одометр поездки 1"""

    _attr_name = "Trip Meter 1"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:road-variant"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def _get_sensor_type(self) -> str:
        return "trip_meter_1"

    @property
    def native_value(self) -> float:
        """Вернуть расстояние"""
        parser = self._get_parser()
        if parser:
            movement = parser.get_movement_info()
            return round(movement['trip_meter_1'], 1)
        return None


class ZeekrTripMeter2Sensor(ZeekrBaseSensor):
    """Одометр поездки 2"""

    _attr_name = "Trip Meter 2"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:road-variant"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def _get_sensor_type(self) -> str:
        return "trip_meter_2"

    @property
    def native_value(self) -> float:
        """Вернуть расстояние"""
        parser = self._get_parser()
        if parser:
            movement = parser.get_movement_info()
            return round(movement['trip_meter_2'], 1)
        return None


# ==================== 🔧 ОБСЛУЖИВАНИЕ (РАСШИРЕНО) ====================

class ZeekrEngineHoursToServiceSensor(ZeekrBaseSensor):
    """Часов до ТО"""

    _attr_name = "Engine Hours to Service"
    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:wrench-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "engine_hours_to_service"

    @property
    def native_value(self) -> int:
        """Вернуть часы"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return maintenance['engine_hours_to_service']
        return None


class ZeekrBrakeFluidLevelSensor(ZeekrBaseSensor):
    """Уровень тормозной жидкости"""

    _attr_name = "Brake Fluid Level"
    _attr_icon = "mdi:water-opacity"

    def _get_sensor_type(self) -> str:
        return "brake_fluid_level"

    @property
    def native_value(self) -> str:
        """Вернуть уровень"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return maintenance['brake_fluid_level']
        return "Неизвестно"


class ZeekrWasherFluidLevelSensor(ZeekrBaseSensor):
    """Уровень жидкости омывателя"""

    _attr_name = "Washer Fluid Level"
    _attr_icon = "mdi:water-opacity"

    def _get_sensor_type(self) -> str:
        return "washer_fluid_level"

    @property
    def native_value(self) -> str:
        """Вернуть уровень"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return maintenance['washer_fluid_level']
        return "Неизвестно"


class ZeekrEngineCoolantLevelSensor(ZeekrBaseSensor):
    """Уровень охлаждающей жидкости"""

    _attr_name = "Engine Coolant Level"
    _attr_icon = "mdi:water-opacity"

    def _get_sensor_type(self) -> str:
        return "engine_coolant_level"

    @property
    def native_value(self) -> str:
        """Вернуть уровень"""
        parser = self._get_parser()
        if parser:
            maintenance = parser.get_maintenance_info()
            return maintenance['engine_coolant_level']
        return "Неизвестно"


# ==================== 💨 ВОЗДУХ (РАСШИРЕНО) ====================

class ZeekrExteriorPM25LevelSensor(ZeekrBaseSensor):
    """Уровень PM2.5 снаружи"""

    _attr_name = "Exterior PM2.5 Level"
    _attr_icon = "mdi:air-filter"

    def _get_sensor_type(self) -> str:
        return "exterior_pm25_level"

    @property
    def native_value(self) -> str:
        """Вернуть уровень"""
        parser = self._get_parser()
        if parser:
            pollution = parser.get_pollution_info()
            return pollution['exterior_pm25_level']
        return None


class ZeekrRelativeHumiditySensor(ZeekrBaseSensor):
    """Относительная влажность воздуха"""

    _attr_name = "Relative Humidity"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:water-percent"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "relative_humidity"

    @property
    def native_value(self) -> int:
        """Вернуть влажность"""
        parser = self._get_parser()
        if parser:
            pollution = parser.get_pollution_info()
            return pollution['relative_humidity']
        return None


# ==================== 🅿️ ПАРКОВКА ====================

class ZeekrParkDurationSensor(ZeekrBaseSensor):
    """Длительность парковки"""

    _attr_name = "Park Duration"
    _attr_icon = "mdi:parking"

    def _get_sensor_type(self) -> str:
        return "park_duration"

    @property
    def native_value(self) -> str:
        """Вернуть длительность"""
        parser = self._get_parser()
        if parser:
            park = parser.get_park_info()
            return park['park_duration']
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Дополнительные атрибуты"""
        parser = self._get_parser()
        if parser:
            park = parser.get_park_info()
            return {
                'parked_since': park['parked_since'],
                'total_seconds': park['total_seconds'],
                'is_parked': park['is_parked'],
            }
        return {}


# ==================== 🎯 КЛИМАТ (РАСШИРЕНО) ====================

class ZeekrSteeringWheelHeatingStatusSensor(ZeekrBaseSensor):
    """Статус обогрева руля"""

    _attr_name = "Steering Wheel Heating"
    _attr_icon = "mdi:heating"

    def _get_sensor_type(self) -> str:
        return "steering_wheel_heating"

    @property
    def native_value(self) -> str:
        """Вернуть статус"""
        parser = self._get_parser()
        if parser:
            climate = parser.get_climate_info()
            return climate['steering_wheel_heating']
        return None


class ZeekrDriverHeatingStatusSensor(ZeekrBaseSensor):
    """Статус обогрева водителя"""

    _attr_name = "Driver Heating"
    _attr_icon = "mdi:heating"

    def _get_sensor_type(self) -> str:
        return "driver_heating"

    @property
    def native_value(self) -> str:
        """Вернуть статус"""
        parser = self._get_parser()
        if parser:
            climate = parser.get_climate_info()
            return climate['driver_heating']
        return None


class ZeekrPassengerHeatingStatusSensor(ZeekrBaseSensor):
    """Статус обогрева пассажира"""

    _attr_name = "Passenger Heating"
    _attr_icon = "mdi:heating"

    def _get_sensor_type(self) -> str:
        return "passenger_heating"

    @property
    def native_value(self) -> str:
        """Вернуть статус"""
        parser = self._get_parser()
        if parser:
            climate = parser.get_climate_info()
            return climate['passenger_heating']
        return None


# ==================== 📍 КООРДИНАТЫ ====================

class ZeekrLatitudeSensor(ZeekrBaseSensor):
    """Широта (для статистики и логирования)"""

    _attr_name = "Latitude"
    _attr_icon = "mdi:latitude"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "latitude"

    @property
    def native_value(self) -> float:
        """Вернуть широту"""
        parser = self._get_parser()
        if parser:
            position = parser.get_position_info()
            return round(position['latitude'], 6)
        return None


class ZeekrLongitudeSensor(ZeekrBaseSensor):
    """Долгота (для статистики и логирования)"""

    _attr_name = "Longitude"
    _attr_icon = "mdi:longitude"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "longitude"

    @property
    def native_value(self) -> float:
        """Вернуть долготу"""
        parser = self._get_parser()
        if parser:
            position = parser.get_position_info()
            return round(position['longitude'], 6)
        return None


class ZeekrAltitudeSensor(ZeekrBaseSensor):
    """Высота над уровнем моря"""

    _attr_name = "Altitude"
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_icon = "mdi:elevation-rise"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "altitude"

    @property
    def native_value(self) -> int:
        """Вернуть высоту"""
        parser = self._get_parser()
        if parser:
            position = parser.get_position_info()
            return position['altitude']
        return None


# ==================== 🔐 ИНФОРМАЦИЯ ====================

class ZeekrPropulsionTypeSensor(ZeekrBaseSensor):
    """Тип пропульсии"""

    _attr_name = "Propulsion Type"
    _attr_icon = "mdi:fuel-cell"

    def _get_sensor_type(self) -> str:
        return "propulsion_type"

    @property
    def native_value(self) -> str:
        """Вернуть тип"""
        parser = self._get_parser()
        if parser:
            return parser.get_propulsion_type()
        return None

# ==================== ⚡ ЗАРЯДКА ====================

class ZeekrChargePileVoltageSensor(ZeekrBaseSensor):
    """Вольтаж на зарядке"""

    _attr_name = "Charge Pile Voltage"
    _attr_native_unit_of_measurement = "V"
    _attr_icon = "mdi:flash"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "charge_pile_voltage"

    @property
    def native_value(self) -> float:
        """Вернуть вольтаж на зарядке"""
        parser = self._get_parser()
        if parser:
            charging = parser.get_charging_info()
            return round(charging['charge_pile_voltage'], 1)
        return None


class ZeekrCurrentPowerInputSensor(ZeekrBaseSensor):
    """Текущая мощность входа (кВт приходит на машину)"""

    _attr_name = "Current Power Input"
    _attr_native_unit_of_measurement = "kW"
    _attr_icon = "mdi:flash-outline"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "current_power_input"

    @property
    def native_value(self) -> float:
        """Вернуть текущую мощность входа"""
        parser = self._get_parser()
        if parser:
            charging = parser.get_charging_info()
            return round(charging['current_power_input'], 1)
        return None


class ZeekrDCChargeCurrentSensor(ZeekrBaseSensor):
    """Ток DC зарядки"""

    _attr_name = "DC Charge Current"
    _attr_native_unit_of_measurement = "A"
    _attr_icon = "mdi:lightning-bolt"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "dc_charge_current"

    @property
    def native_value(self) -> float:
        """Вернуть ток DC зарядки"""
        parser = self._get_parser()
        if parser:
            charging = parser.get_charging_info()
            return round(charging['dc_charge_pile_current'], 1)
        return None


class ZeekrChargeStatusSensor(ZeekrBaseSensor):
    """Статус зарядки"""

    _attr_name = "Charge Status"
    _attr_icon = "mdi:battery-charging-wireless"

    def _get_sensor_type(self) -> str:
        return "charge_status_sensor"

    @property
    def native_value(self) -> str:
        """Вернуть статус зарядки"""
        parser = self._get_parser()
        if parser:
            charging = parser.get_charging_info()
            return charging['charge_status']
        return None
class ZeekrChargeInputPowerSensor(ZeekrBaseSensor):
    """Текущая мощность входа при зарядке (кВт)"""

    _attr_name = "Charge Input Power"
    _attr_native_unit_of_measurement = "kW"
    _attr_icon = "mdi:lightning-bolt"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _get_sensor_type(self) -> str:
        return "charge_input_power"

    @property
    def native_value(self) -> int:
        """Вернуть кВт входа при зарядке"""
        parser = self._get_parser()
        if parser:
            battery = parser.get_battery_info()
            return int(battery['charge_level'])  # 🎯 это кВт входа
        return None