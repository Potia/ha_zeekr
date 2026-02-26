# custom_components/zeekr/sensor.py
"""Sensor platform for Zeekr integration"""

import logging
from typing import Any, Dict

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
from vehicle_parser import VehicleDataParser

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
            ZeekrBatterySensor(coordinator, vin),
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
            # НОВЫЕ ДАТЧИКИ:
            ZeekrMainBatteryVoltageSensor(coordinator, vin),
            ZeekrParkTimeSensor(coordinator, vin),
            ZeekrLastUpdateTimeSensor(coordinator, vin),
        ])

    async_add_entities(entities)


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


class ZeekrBatterySensor(ZeekrBaseSensor):
    """Battery charge level sensor"""

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
            return battery['charge_level']
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

    class ZeekrMainBatteryVoltageSensor(ZeekrBaseSensor):
        """Main battery voltage (12V) sensor"""

        _attr_name = "Main Battery Voltage"
        _attr_native_unit_of_measurement = "V"
        _attr_icon = "mdi:battery-12v"
        _attr_state_class = SensorStateClass.MEASUREMENT
        _attr_device_class = SensorDeviceClass.VOLTAGE

        def _get_sensor_type(self) -> str:
            return "main_battery_voltage"

        @property
        def native_value(self) -> float:
            """Return main battery voltage"""
            parser = self._get_parser()
            if parser:
                maintenance = parser.data.get('additionalVehicleStatus', {}).get('maintenanceStatus', {})
                battery_info = maintenance.get('mainBatteryStatus', {})
                voltage = float(battery_info.get('voltage', 0))
                return round(voltage, 2)
            return None

    class ZeekrParkTimeSensor(ZeekrBaseSensor):
        """Park time sensor"""

        _attr_name = "Park Time"
        _attr_icon = "mdi:clock"
        _attr_state_class = SensorStateClass.MEASUREMENT

        def _get_sensor_type(self) -> str:
            return "park_time"

        @property
        def native_value(self) -> str:
            """Return park time"""
            parser = self._get_parser()
            if parser:
                park_time_ms = int(parser.data.get('parkTime', {}).get('status', 0))
                if park_time_ms == 0:
                    return "Едет / Не припаркован"

                # Преобразуем миллисекунды в время припаркованности
                from datetime import datetime, timedelta
                park_datetime = datetime.fromtimestamp(park_time_ms / 1000)
                current_time = datetime.now()

                # Вычисляем как долго припаркован
                park_duration = current_time - park_datetime

                # Форматируем в дни, часы, минуты
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
            return None

        @property
        def extra_state_attributes(self) -> Dict[str, Any]:
            """Return additional attributes"""
            parser = self._get_parser()
            if parser:
                park_time_ms = int(parser.data.get('parkTime', {}).get('status', 0))
                if park_time_ms > 0:
                    from datetime import datetime
                    park_datetime = datetime.fromtimestamp(park_time_ms / 1000)
                    return {
                        "parked_since": park_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    }
            return {}

    class ZeekrLastUpdateTimeSensor(ZeekrBaseSensor):
        """Last update time sensor - when vehicle last connected to server"""

        _attr_name = "Last Update Time"
        _attr_icon = "mdi:cloud-upload"
        _attr_state_class = SensorStateClass.MEASUREMENT

        def _get_sensor_type(self) -> str:
            return "last_update_time"

        @property
        def native_value(self) -> str:
            """Return last update time"""
            parser = self._get_parser()
            if parser:
                timestamp = int(parser.data.get('updateTime', 0))
                if timestamp:
                    from datetime import datetime
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
                    from datetime import datetime
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