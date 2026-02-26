# vehicle_parser.py
"""
Парсер данных автомобиля - извлечение и форматирование информации
"""
from typing import Dict, Any, Optional
from datetime import datetime


class VehicleDataParser:
    """Парсер для извлечения основной информации о статусе автомобиля"""

    def __init__(self, raw_data: Dict[str, Any]):
        """
        Инициализация парсера

        Args:
            raw_data: Полные данные статуса автомобиля из API
        """
        self.data = raw_data

    # ==================== БАЗОВАЯ ИНФОРМАЦИЯ ====================

    def get_vin(self) -> str:
        """Получает VIN номер автомобиля"""
        return self.data.get('configuration', {}).get('vin', 'N/A')

    def get_engine_status(self) -> str:
        """Получает статус двигателя"""
        status = self.data.get('basicVehicleStatus', {}).get('engineStatus', 'unknown')
        return '✅ Работает' if status == 'engine_on' else '❌ Выключен'

    def get_last_update_time(self) -> str:
        """Получает время последнего обновления"""
        timestamp = int(self.data.get('updateTime', 0))
        if timestamp:
            dt = datetime.fromtimestamp(timestamp / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'

    # ==================== БАТАРЕЯ И ЗАРЯД ====================

    def get_battery_info(self) -> Dict[str, Any]:
        """Получает информацию о батарее"""
        ev_status = self.data.get('additionalVehicleStatus', {}).get('electricVehicleStatus', {})

        return {
            'charge_level': int(ev_status.get('chargeLevel', 0)),
            'distance_to_empty': int(ev_status.get('distanceToEmptyOnBatteryOnly', 0)),
            'charge_status': self._parse_charge_status(ev_status.get('chargeSts', '0')),
            'avg_power_consumption': float(ev_status.get('averPowerConsumption', 0)),
            'time_to_fully_charged': int(ev_status.get('timeToFullyCharged', 0)),
        }

    def _parse_charge_status(self, status_code: str) -> str:
        """Переводит код статуса заряда на русский"""
        status_map = {
            '0': 'Неизвестно',
            '1': 'Не подключено',
            '2': 'Подключено',
            '3': 'Зарядка завершена',
            '4': 'Зарядка',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ТЕМПЕРАТУРА ====================

    def get_temperature_info(self) -> Dict[str, Any]:
        """Получает информацию о температуре"""
        climate = self.data.get('additionalVehicleStatus', {}).get('climateStatus', {})

        return {
            'interior_temp': float(climate.get('interiorTemp', 0)),
            'exterior_temp': float(climate.get('exteriorTemp', 0)),
        }

    # ==================== ПОЛОЖЕНИЕ И КООРДИНАТЫ ====================

    def get_position_info(self) -> Dict[str, Any]:
        """Получает информацию о положении автомобиля"""
        position = self.data.get('basicVehicleStatus', {}).get('position', {})

        # Координаты в формате целых чисел (умножены на 1e6)
        latitude = int(position.get('latitude', 0)) / 1e7  # ← ИЗМЕНИТЕ 1e6 на 1e7
        longitude = int(position.get('longitude', 0)) / 1e7  # ← ИЗМЕНИТЕ 1e6 на 1e7

        return {
            'latitude': latitude,
            'longitude': longitude,
            'altitude': int(position.get('altitude', 0)),
            'direction': int(position.get('direction', 0)),
        }

    # ==================== ДВЕРИ И БЕЗОПАСНОСТЬ ====================

    def get_security_info(self) -> Dict[str, bool]:
        """Получает информацию о безопасности"""
        safety = self.data.get('additionalVehicleStatus', {}).get('drivingSafetyStatus', {})

        return {
            'driver_door_open': bool(int(safety.get('doorOpenStatusDriver', 0))),
            'passenger_door_open': bool(int(safety.get('doorOpenStatusPassenger', 0))),
            'driver_rear_door_open': bool(int(safety.get('doorOpenStatusDriverRear', 0))),
            'passenger_rear_door_open': bool(int(safety.get('doorOpenStatusPassengerRear', 0))),
            'trunk_open': bool(int(safety.get('trunkOpenStatus', 0))),
            'engine_hood_open': bool(int(safety.get('engineHoodOpenStatus', 0))),
            'central_lock': self._parse_lock_status(safety.get('centralLockingStatus', '0')),
        }

    def _parse_lock_status(self, status_code: str) -> str:
        """Переводит код статуса замка"""
        status_map = {
            '0': 'Неизвестно',
            '1': 'Заблокировано',
            '2': 'Разблокировано',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ОКНА ====================

    def get_windows_info(self) -> Dict[str, Any]:
        """Получает информацию об окнах"""
        climate = self.data.get('additionalVehicleStatus', {}).get('climateStatus', {})

        return {
            'driver_window': self._parse_window_status(climate.get('winStatusDriver', '0')),
            'passenger_window': self._parse_window_status(climate.get('winStatusPassenger', '0')),
            'driver_rear_window': self._parse_window_status(climate.get('winStatusDriverRear', '0')),
            'passenger_rear_window': self._parse_window_status(climate.get('winStatusPassengerRear', '0')),
        }

    def _parse_window_status(self, status_code: str) -> str:
        """Переводит код статуса окна"""
        status_map = {
            '0': 'Открыто',
            '1': 'Открывается',
            '2': 'Закрыто',
            '3': 'Закрывается',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ШИНЫ ====================

    def get_tires_info(self) -> Dict[str, float]:
        """Получает информацию о давлении в шинах"""
        maintenance = self.data.get('additionalVehicleStatus', {}).get('maintenanceStatus', {})

        return {
            'driver_tire': float(maintenance.get('tyreStatusDriver', 0)),
            'passenger_tire': float(maintenance.get('tyreStatusPassenger', 0)),
            'driver_rear_tire': float(maintenance.get('tyreStatusDriverRear', 0)),
            'passenger_rear_tire': float(maintenance.get('tyreStatusPassengerRear', 0)),
        }

    # ==================== ОДОМЕТР И ТО ====================

    def get_maintenance_info(self) -> Dict[str, Any]:
        """Получает информацию о техническом обслуживании"""
        maintenance = self.data.get('additionalVehicleStatus', {}).get('maintenanceStatus', {})

        return {
            'odometer': float(maintenance.get('odometer', 0)),
            'days_to_service': int(maintenance.get('daysToService', 0)),
            'distance_to_service': int(maintenance.get('distanceToService', 0)),
        }

    # ==================== СКОРОСТЬ И ДВИЖЕНИЕ ====================

    def get_movement_info(self) -> Dict[str, Any]:
        """Получает информацию о движении"""
        basic = self.data.get('basicVehicleStatus', {})
        running = self.data.get('additionalVehicleStatus', {}).get('runningStatus', {})

        return {
            'speed': float(basic.get('speed', 0)),
            'avg_speed': int(running.get('avgSpeed', 0)),
            'trip_meter_1': float(running.get('tripMeter1', 0)),
            'trip_meter_2': float(running.get('tripMeter2', 0)),
            'direction': int(basic.get('direction', 0)),  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
        }

    # ==================== ЗАГРЯЗНЕНИЕ ====================

    def get_pollution_info(self) -> Dict[str, Any]:
        """Получает информацию о качестве воздуха"""
        pollution = self.data.get('additionalVehicleStatus', {}).get('pollutionStatus', {})

        return {
            'interior_pm25': int(pollution.get('interiorPM25', 0)),
            'interior_pm25_level': self._parse_pm25_level(pollution.get('interiorPM25Level', '0')),
        }

    def _parse_pm25_level(self, level_code: str) -> str:
        """Переводит уровень PM2.5"""
        level_map = {
            '0': 'Отличный',
            '1': 'Хороший',
            '2': 'Умеренный',
            '3': 'Плохой',
            '4': 'Очень плохой',
        }
        return level_map.get(str(level_code), 'Неизвестно')

    # ==================== ПОЛНЫЙ ОТЧЕТ ====================

    def get_full_summary(self) -> str:
        """Возвращает полный красиво отформатированный отчет"""

        battery = self.get_battery_info()
        temp = self.get_temperature_info()
        position = self.get_position_info()
        security = self.get_security_info()
        windows = self.get_windows_info()
        tires = self.get_tires_info()
        maintenance = self.get_maintenance_info()
        movement = self.get_movement_info()
        pollution = self.get_pollution_info()

        report = f"""
{'=' * 80}
🚗 ПОЛНЫЙ ОТЧЕТ О СОСТОЯНИИ АВТОМОБИЛЯ
{'=' * 80}

📊 ОСНОВНАЯ ИНФОРМАЦИЯ
{'-' * 80}
VIN:                    {self.get_vin()}
Статус двигателя:       {self.get_engine_status()}
Последнее обновление:   {self.get_last_update_time()}

🔋 БАТАРЕЯ И ЗАРЯД
{'-' * 80}
Уровень заряда:         {battery['charge_level']}%
Статус зарядки:         {battery['charge_status']}
Запас хода:             {battery['distance_to_empty']} км
Среднее потребление:    {battery['avg_power_consumption']} кВт
Время до полной зарядки: {battery['time_to_fully_charged']} мин

🌡️  ТЕМПЕРАТУРА
{'-' * 80}
Внутренняя температура: {temp['interior_temp']}°C
Внешняя температура:    {temp['exterior_temp']}°C

📍 ПОЛОЖЕНИЕ
{'-' * 80}
Широта:                 {position['latitude']:.6f}
Долгота:                {position['longitude']:.6f}
Высота:                 {position['altitude']} м
Направление:            {position['direction']}°

🔒 БЕЗОПАСНОСТЬ И ДВЕРИ
{'-' * 80}
Центральный замок:      {security['central_lock']}
Дверь водителя:         {'🔓 Открыта' if security['driver_door_open'] else '🔐 Закрыта'}
Дверь пассажира:        {'🔓 Открыта' if security['passenger_door_open'] else '🔐 Закрыта'}
Задняя дверь водителя:  {'🔓 Открыта' if security['driver_rear_door_open'] else '🔐 Закрыта'}
Задняя дверь пассажира: {'🔓 Открыта' if security['passenger_rear_door_open'] else '🔐 Закрыта'}
Багажник:               {'🔓 Открыт' if security['trunk_open'] else '🔐 Закрыт'}
Капот:                  {'🔓 Открыт' if security['engine_hood_open'] else '🔐 Закрыт'}

🪟 ОКНА
{'-' * 80}
Окно водителя:          {windows['driver_window']}
Окно пассажира:         {windows['passenger_window']}
Заднее окно водителя:   {windows['driver_rear_window']}
Заднее окно пассажира:  {windows['passenger_rear_window']}

🛞 ШИНЫ (Давление в кПа)
{'-' * 80}
Передняя левая:         {tires['driver_tire']:.1f}
Передняя правая:        {tires['passenger_tire']:.1f}
Задняя левая:           {tires['driver_rear_tire']:.1f}
Задняя правая:          {tires['passenger_rear_tire']:.1f}

🔧 ТЕХНИЧЕСКОЕ ОБСЛУЖИВАНИЕ
{'-' * 80}
Одометр:                {maintenance['odometer']:.0f} км
Дней до ТО:             {maintenance['days_to_service']}
Км до ТО:               {maintenance['distance_to_service']} км

🚙 ДВИЖЕНИЕ
{'-'*80}
Текущая скорость:       {movement['speed']:.1f} км/ч
Средняя скорость:       {movement['avg_speed']} км/ч
Одометр 1:              {movement['trip_meter_1']:.1f} км
Одометр 2:              {movement['trip_meter_2']:.1f} км
Направление:            {movement['direction']}°

💨 КАЧЕСТВО ВОЗДУХА
{'-' * 80}
PM2.5 внутри:           {pollution['interior_pm25']} мкг/м³
Уровень качества:       {pollution['interior_pm25_level']}

{'=' * 80}
"""
        return report