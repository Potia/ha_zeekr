# custom_components/zeekr/vehicle_parser.py
"""
Парсер данных автомобиля - извлечение и форматирование информации
"""
from typing import Dict, Any, Optional
from datetime import datetime


class VehicleDataParser:
    """Парсер для извлечения всей информации о статусе автомобиля"""

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

    def get_propulsion_type(self) -> str:
        """Получает тип пропульсии (электро, гибрид и т.д.)"""
        propulsion_map = {
            '0': 'Бензин',
            '1': 'Дизель',
            '2': 'Гибрид',
            '3': 'Plug-in гибрид',
            '4': 'Электро',
        }
        prop_type = self.data.get('configuration', {}).get('propulsionType', '0')
        return propulsion_map.get(str(prop_type), 'Неизвестно')

    # ==================== БАТАРЕЯ И ЗАРЯД ====================

    def get_battery_info(self) -> Dict[str, Any]:
        """Получает информацию о батерее"""
        ev_status = self.data.get('additionalVehicleStatus', {}).get('electricVehicleStatus', {})
        main_battery = self.data.get('additionalVehicleStatus', {}).get('maintenanceStatus', {}).get(
            'mainBatteryStatus', {})

        return {
            # 🎯 ОСНОВНАЯ БАТАРЕЯ (%)
            'battery_percentage': int(float(ev_status.get('chargeLevel', 0))),  # 71%

            'distance_to_empty': int(float(ev_status.get('distanceToEmptyOnBatteryOnly', 0))),
            'charge_status': self._parse_charge_status(ev_status.get('chargeSts', '0')),
            'avg_power_consumption': float(ev_status.get('averPowerConsumption', 0)),  # 24.2 кВт
            'time_to_fully_charged': int(float(ev_status.get('timeToFullyCharged', 0))),

            # 🎯 12V БАТАРЕЯ (вспомогательная)
            'aux_battery_percentage': float(main_battery.get('chargeLevel', 0)),  # 98.4%
            'aux_battery_voltage': float(main_battery.get('voltage', 0)),  # 12.225V ✅ ИСПРАВЛЕНО!

            # Неизвестные параметры
            'soc': float(ev_status.get('stateOfCharge', 0)),
            'soh': float(ev_status.get('stateOfHealth', 0)),

            # Температура батареи
            'hv_temp_level': self._parse_hv_temp_level(ev_status.get('hvTempLevel', '0')),
            'hv_temp_level_numeric': int(ev_status.get('hvTempLevel', 0)),
        }

    def _parse_hv_temp_level(self, level_code: str) -> str:
        """Переводит уровень температуры батареи"""
        temp_map = {
            '0': 'Неизвестно',
            '1': 'Теплая 🔥',
            '2': 'Немного холодная ❄️',
            '3': 'Холодная 🥶',
            '4': 'Сильно холодная 🧊',
        }
        return temp_map.get(str(level_code), 'Неизвестно')

    def _parse_charge_status(self, status_code: str) -> str:
        """Переводит код статуса заряда на русский"""
        status_map = {
            '0': 'Не подключено',
            '1': 'Подключено (ожидание)',
            '2': 'Предзарядка',
            '3': 'Зарядка',
            '4': 'Зарядка завершена',
            '5': 'Приостановлено',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ТЕМПЕРАТУРА ====================

    def get_temperature_info(self) -> Dict[str, Any]:
        """Получает информацию о температуре"""
        climate = self.data.get('additionalVehicleStatus', {}).get('climateStatus', {})

        return {
            'interior_temp': float(climate.get('interiorTemp', 0)),
            'exterior_temp': float(climate.get('exteriorTemp', 0)),
            'cabin_temp_reduction_status': bool(climate.get('cabinTempReductionStatus', 0)),
            'climate_over_heat_proactive': bool(climate.get('climateOverHeatProActive', 'false') == 'true'),
        }

    # ==================== ПОЛОЖЕНИЕ И КООРДИНАТЫ ====================

    def get_position_info(self) -> Dict[str, Any]:
        """Получает информацию о положении автомобиля"""
        position = self.data.get('basicVehicleStatus', {}).get('position', {})

        # Проверяем есть ли данные координат
        latitude_raw = position.get('latitude', '')
        longitude_raw = position.get('longitude', '')

        if latitude_raw and longitude_raw:
            # Преобразуем из целых чисел в градусы
            latitude = int(latitude_raw) / 1e7
            longitude = int(longitude_raw) / 1e7
        else:
            latitude = 0.0
            longitude = 0.0

        return {
            'latitude': latitude,
            'longitude': longitude,
            'altitude': int(position.get('altitude', 0)) if position.get('altitude') else 0,
            'direction': int(position.get('direction', 0)) if position.get('direction') else 0,
            'can_be_trusted': bool(position.get('posCanBeTrusted', 'false') == 'true'),
        }

    # ==================== ДВЕРИ И БЕЗОПАСНОСТЬ ====================

    def get_security_info(self) -> Dict[str, Any]:
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
            'driver_lock': self._parse_lock_status(safety.get('doorLockStatusDriver', '0')),
            'passenger_lock': self._parse_lock_status(safety.get('doorLockStatusPassenger', '0')),
            'driver_rear_lock': self._parse_lock_status(safety.get('doorLockStatusDriverRear', '0')),
            'passenger_rear_lock': self._parse_lock_status(safety.get('doorLockStatusPassengerRear', '0')),
            'trunk_lock': self._parse_lock_status(safety.get('trunkLockStatus', '0')),
            'electric_park_brake': self._parse_park_brake(safety.get('electricParkBrakeStatus', '0')),
            'srs_crash_status': bool(int(safety.get('srsCrashStatus', 0))),
            'alarm_status': safety.get('vehicleAlarm', {}).get('alrmSt', '0'),
        }

    def _parse_lock_status(self, status_code: str) -> str:
        """Переводит код статуса замка"""
        status_map = {
            '0': 'Неизвестно',
            '1': 'Заблокировано',
            '2': 'Разблокировано',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    def _parse_park_brake(self, status_code: str) -> str:
        """Переводит статус электронного тормоза парковки"""
        status_map = {
            '0': 'Выключено',
            '1': 'Включено',
            '2': 'Ошибка',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ОКНА ====================

    def get_windows_info(self) -> Dict[str, Any]:
        """Получает информацию об окнах и люке"""
        climate = self.data.get('additionalVehicleStatus', {}).get('climateStatus', {})

        return {
            'driver_window': self._parse_window_status(climate.get('winStatusDriver', '2')),
            'passenger_window': self._parse_window_status(climate.get('winStatusPassenger', '2')),
            'driver_rear_window': self._parse_window_status(climate.get('winStatusDriverRear', '2')),
            'passenger_rear_window': self._parse_window_status(climate.get('winStatusPassengerRear', '2')),
            'sunroof_position': int(climate.get('sunroofPos', 0)),
            'sunroof_open': bool(int(climate.get('sunroofOpenStatus', 0))),
            'sunroof_rear_open': bool(int(climate.get('sunCurtainRearOpenStatus', 0))),
            'window_close_reminder': self._parse_window_reminder(climate.get('winCloseReminder', '0')),
            'defrost': bool(climate.get('defrost', 'false') == 'true'),
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

    def _parse_window_reminder(self, code: str) -> str:
        """Парсит напоминание о закрытии окна"""
        map_reminder = {
            '0': 'Нет напоминания',
            '1': 'Окна приоткрыты',
            '2': 'Окна открыты',
            '3': 'Нужно закрыть окна',
        }
        return map_reminder.get(str(code), 'Неизвестно')

    # ==================== КЛИМАТ ====================

    def get_climate_info(self) -> Dict[str, Any]:
        """Получает детальную информацию о климате"""
        climate = self.data.get('additionalVehicleStatus', {}).get('climateStatus', {})

        return {
            'interior_temp': float(climate.get('interiorTemp', 0)),
            'exterior_temp': float(climate.get('exteriorTemp', 0)),
            'steering_wheel_heating': self._parse_heating_status(climate.get('steerWhlHeatingSts', '0')),
            'driver_heating': self._parse_heating_status(climate.get('drvHeatSts', '0')),
            'passenger_heating': self._parse_heating_status(climate.get('passHeatingSts', '0')),
            'air_blower_active': bool(climate.get('airBlowerActive', 'false') == 'true'),
            'pre_climate_active': bool(climate.get('preClimateActive', 'false') == 'true'),
            'cds_climate_active': bool(climate.get('cdsClimateActive', 'false') == 'true'),
        }

    def _parse_heating_status(self, status_code: str) -> str:
        """Парсит статус обогрева"""
        status_map = {
            '0': 'Выключено',
            '1': 'Уровень 1',
            '2': 'Уровень 2',
            '3': 'Уровень 3',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ШИНЫ ====================

    def get_tires_info(self) -> Dict[str, Any]:
        """Получает информацию о давлении в шинах"""
        maintenance = self.data.get('additionalVehicleStatus', {}).get('maintenanceStatus', {})

        return {
            'driver_tire': float(maintenance.get('tyreStatusDriver', 0)),
            'passenger_tire': float(maintenance.get('tyreStatusPassenger', 0)),
            'driver_rear_tire': float(maintenance.get('tyreStatusDriverRear', 0)),
            'passenger_rear_tire': float(maintenance.get('tyreStatusPassengerRear', 0)),
            'driver_temp': float(maintenance.get('tyreTempDriver', 0)),
            'passenger_temp': float(maintenance.get('tyreTempPassenger', 0)),
            'driver_rear_temp': float(maintenance.get('tyreTempDriverRear', 0)),
            'passenger_rear_temp': float(maintenance.get('tyreTempPassengerRear', 0)),
        }

    # ==================== ОДОМЕТР И ТО ====================

    def get_maintenance_info(self) -> Dict[str, Any]:
        """Получает информацию о техническом обслуживании"""
        maintenance = self.data.get('additionalVehicleStatus', {}).get('maintenanceStatus', {})

        return {
            'odometer': float(maintenance.get('odometer', 0)),
            'days_to_service': int(maintenance.get('daysToService', 0)),
            'distance_to_service': int(maintenance.get('distanceToService', 0)),
            'engine_hours_to_service': int(maintenance.get('engineHrsToService', 0)),
            'service_warning_status': bool(int(maintenance.get('serviceWarningStatus', 0))),
            'brake_fluid_level': self._parse_fluid_level(maintenance.get('brakeFluidLevelStatus', '0')),
            'washer_fluid_level': self._parse_fluid_level(maintenance.get('washerFluidLevelStatus', '0')),
            'engine_coolant_level': self._parse_fluid_level(maintenance.get('engineCoolantLevelStatus', '0')),
        }

    def _parse_fluid_level(self, level_code: str) -> str:
        """Парсит уровень жидкостей"""
        level_map = {
            '0': 'Низко 🟡',  # washerFluidLevelStatus: 0 - низко
            '1': 'Нормально 🟢',
            '2': 'Хорошо 🟢',
            '3': 'Полный 🟢',  # brakeFluidLevelStatus: 3 - полный, engineCoolantLevelStatus: 3 - полный
        }
        return level_map.get(str(level_code), 'Неизвестно')

    # ==================== СКОРОСТЬ И ДВИЖЕНИЕ ====================

    def get_movement_info(self) -> Dict[str, Any]:
        """Получает информацию о движении"""
        basic = self.data.get('basicVehicleStatus', {})
        running = self.data.get('additionalVehicleStatus', {}).get('runningStatus', {})

        return {
            'speed': float(basic.get('speed', 0)),
            'speed_valid': bool(basic.get('speedValidity', 'false') == 'true'),
            'avg_speed': int(float(running.get('avgSpeed', 0))),
            'trip_meter_1': float(running.get('tripMeter1', 0)),
            'trip_meter_2': float(running.get('tripMeter2', 0)),
            'direction': int(basic.get('direction', 0)) if basic.get('direction') else 0,
        }

    # ==================== ОГНИ И СИГНАЛЫ ====================

    def get_lights_info(self) -> Dict[str, bool]:
        """Получает информацию об огнях"""
        running = self.data.get('additionalVehicleStatus', {}).get('runningStatus', {})

        return {
            'hi_beam': bool(int(running.get('hiBeam', 0))),
            'lo_beam': bool(int(running.get('loBeam', 0))),
            'drl': bool(int(running.get('drl', 0))),  # DRL = Daytime Running Lights
            'front_fog': bool(int(running.get('frntFog', 0))),
            'rear_fog': bool(int(running.get('reFog', 0))),
            'stop_lights': bool(int(running.get('stopLi', 0))),
            'reverse_lights': bool(int(running.get('reverseLi', 0))),
            'flash': bool(int(running.get('flash', 0))),
            'welcome': bool(int(running.get('welcome', 0))),
            'goodbye': bool(int(running.get('goodbye', 0))),
            'home_safe': bool(int(running.get('homeSafe', 0))),
            'afs': bool(int(running.get('afs', 0))),  # Adaptive Front Lights
        }

    # ==================== ЗАГРЯЗНЕНИЕ ====================

    def get_pollution_info(self) -> Dict[str, Any]:
        """Получает информацию о качестве воздуха"""
        pollution = self.data.get('additionalVehicleStatus', {}).get('pollutionStatus', {})

        return {
            'interior_pm25': int(float(pollution.get('interiorPM25', 0))),
            'interior_pm25_level': self._parse_pm25_level(pollution.get('interiorPM25Level', '0')),
            'exterior_pm25_level': self._parse_pm25_level(pollution.get('exteriorPM25Level', '0')),
            'relative_humidity': int(float(pollution.get('relHumSts', 0))),
        }

    def _parse_pm25_level(self, level_code: str) -> str:
        """Переводит уровень PM2.5"""
        level_map = {
            '0': 'Отличный 🟢',
            '1': 'Хороший 🟢',
            '2': 'Умеренный 🟡',
            '3': 'Плохой 🟠',
            '4': 'Очень плохой 🔴',
        }
        return level_map.get(str(level_code), 'Неизвестно')

    # ==================== ВРЕМЯ ПАРКОВКИ ====================

    def get_park_info(self) -> Dict[str, Any]:
        """Получает информацию о парковке"""
        park_time_ms = int(self.data.get('parkTime', {}).get('status', 0))

        if park_time_ms == 0:
            return {
                'is_parked': False,
                'parked_since': None,
                'park_duration': 'Не припаркован',
                'total_seconds': 0,
            }

        park_datetime = datetime.fromtimestamp(park_time_ms / 1000)
        current_time = datetime.now()
        park_duration = current_time - park_datetime

        total_seconds = int(park_duration.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            duration_str = f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            duration_str = f"{hours}ч {minutes}м"
        else:
            duration_str = f"{minutes}м"

        return {
            'is_parked': True,
            'parked_since': park_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'park_duration': duration_str,
            'total_seconds': total_seconds,
        }

    # ==================== ЗАРЯДКА ====================

    def get_charging_info(self) -> Dict[str, Any]:
        """Получает информацию о зарядке"""
        ev_status = self.data.get('additionalVehicleStatus', {}).get('electricVehicleStatus', {})

        return {
            'charge_status': self._parse_charge_status(ev_status.get('chargeSts', '0')),
            'charge_pile_voltage': float(ev_status.get('dcChargePileUAct', 0)),  # 🎯 Вольтаж на зарядке
            'current_power_input': float(ev_status.get('averPowerConsumption', 0)),  # 🎯 кВт приходит на машину
            'dc_charge_pile_current': float(ev_status.get('dcChargePileIAct', 0)),  # Ток зарядки
            'charge_connector_status': self._parse_charge_connector_status(
                ev_status.get('disChargeConnectStatus', '0')),
            'ac_charge_status': self._parse_charge_status(ev_status.get('chargeSts', '0')),
            'dc_charge_status': self._parse_dc_charge_status(ev_status.get('dcChargeSts', '0')),
        }

    def _parse_charge_connector_status(self, status_code: str) -> str:
        """Парсит статус разъема зарядки"""
        status_map = {
            '0': 'Не подключен',
            '1': 'Подключен',
            '2': 'Ошибка',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    def _parse_dc_charge_status(self, status_code: str) -> str:
        """Парсит статус DC зарядки"""
        status_map = {
            '0': 'Не активна',
            '1': 'Активна',
            '2': 'Завершена',
        }
        return status_map.get(str(status_code), 'Неизвестно')

    # ==================== ТРЕЙЛЕР ====================

    def get_trailer_info(self) -> Dict[str, bool]:
        """Получает информацию о прицепе (если есть)"""
        trailer = self.data.get('additionalVehicleStatus', {}).get('trailerStatus', {})

        return {
            'turning_lamp': bool(int(trailer.get('trailerTurningLampSts', 0))),
            'fog_lamp': bool(int(trailer.get('trailerFogLampSts', 0))),
            'break_lamp': bool(int(trailer.get('trailerBreakLampSts', 0))),
            'reversing_lamp': bool(int(trailer.get('trailerReversingLampSts', 0))),
            'pos_lamp': bool(int(trailer.get('trailerPosLampSts', 0))),
        }

    # ==================== ДОПОЛНИТЕЛЬНО ====================

    def get_gear_status(self) -> Dict[str, Any]:
        """Получает информацию о коробке передач"""
        driving = self.data.get('additionalVehicleStatus', {}).get('drivingBehaviourStatus', {})

        return {
            'gear_auto': bool(int(driving.get('gearAutoStatus', 0))),
            'gear_manual': bool(int(driving.get('gearManualStatus', 0))),
            'engine_speed': float(driving.get('engineSpeed', 0)),
        }

    def get_security_eg_status(self) -> Dict[str, Any]:
        """Получает статус блокировки двигателя (EG - Engine Guard)"""
        eg = self.data.get('eg', {}).get('blocked', {})

        return {
            'eg_blocked': bool(int(eg.get('status', 0))),
        }

    def get_theft_notification(self) -> Dict[str, Any]:
        """Получает информацию о краже"""
        theft = self.data.get('theftNotification', {})

        return {
            'activated': int(theft.get('activated', 0)),
            'time': int(theft.get('time', 0)),
        }

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
        park = self.get_park_info()
        lights = self.get_lights_info()
        climate = self.get_climate_info()
        charging = self.get_charging_info()

        report = f"""
{'=' * 80}
🚗 ПОЛНЫЙ ОТЧЕТ О СОСТОЯНИИ АВТОМОБИЛЯ
{'=' * 80}

📊 ОСНОВНАЯ ИНФОРМАЦИЯ
{'-' * 80}
VIN:                    {self.get_vin()}
Тип пропульсии:         {self.get_propulsion_type()}
Статус двигателя:       {self.get_engine_status()}
Последнее обновление:   {self.get_last_update_time()}

🔋 БАТАРЕЯ И ЗАРЯД
{'-' * 80}
Уровень заряда:         {battery['charge_level']}%
Статус зарядки:         {battery['charge_status']}
Запас хода:             {battery['distance_to_empty']} км
Среднее потребление:    {battery['avg_power_consumption']} кВт
Время до полной зарядки: {battery['time_to_fully_charged']} мин
State of Charge:        {battery['soc']}%
State of Health:        {battery['soh']}%
Напряжение батареи:     {battery['voltage']:.2f}V
Температура батареи:   {battery['hv_temp_level']}

⚡ ИНФОРМАЦИЯ О ЗАРЯДКЕ
{'-' * 80}
Статус зарядки:         {charging['charge_status']}
Вольтаж на зарядке:     {charging['charge_pile_voltage']:.1f}V 🎯
Мощность входа:         {charging['current_power_input']:.1f}кВт 🎯
Ток зарядки DC:         {charging['dc_charge_pile_current']:.1f}A
Статус разъема:         {charging['charge_connector_status']}

🌡️  ТЕМПЕРАТУРА И КЛИМАТ
{'-' * 80}
Внутренняя температура: {temp['interior_temp']}°C
Внешняя температура:    {temp['exterior_temp']}°C
Отопление руля:         {climate['steering_wheel_heating']}
Отопление водителя:     {climate['driver_heating']}
Отопление пассажира:    {climate['passenger_heating']}
Вентилятор включен:     {'Да ✅' if climate['air_blower_active'] else 'Нет ❌'}
Предварительный климат:  {'Активен ✅' if climate['pre_climate_active'] else 'Неактивен ❌'}
Дефрост:                {'Включен ✅' if windows['defrost'] else 'Выключен ❌'}

📍 ПОЛОЖЕНИЕ
{'-' * 80}
Широта:                 {position['latitude']:.6f}
Долгота:                {position['longitude']:.6f}
Высота:                 {position['altitude']} м
Направление:            {position['direction']}°
Координаты доверены:    {'Да ✅' if position['can_be_trusted'] else 'Нет ❌'}

🔒 БЕЗОПАСНОСТЬ И ДВЕРИ
{'-' * 80}
Центральный замок:      {security['central_lock']}
Электрический тормоз:   {security['electric_park_brake']}
Статус SRS:             {'🚨 АКТИВИРОВАНО' if security['srs_crash_status'] else '✅ Ок'}

Дверь водителя:         {'🔓 Открыта' if security['driver_door_open'] else '🔐 Закрыта'} | Замок: {security['driver_lock']}
Дверь пассажира:        {'🔓 Открыта' if security['passenger_door_open'] else '🔐 Закрыта'} | Замок: {security['passenger_lock']}
Задняя дверь водителя:  {'🔓 Открыта' if security['driver_rear_door_open'] else '🔐 Закрыта'} | Замок: {security['driver_rear_lock']}
Задняя дверь пассажира: {'🔓 Открыта' if security['passenger_rear_door_open'] else '🔐 Закрыта'} | Замок: {security['passenger_rear_lock']}
Багажник:               {'🔓 Открыт' if security['trunk_open'] else '🔐 Закрыт'} | Замок: {security['trunk_lock']}
Капот:                  {'🔓 Открыт' if security['engine_hood_open'] else '🔐 Закрыт'}

🪟 ОКНА И ЛЮК
{'-' * 80}
Окно водителя:          {windows['driver_window']}
Окно пассажира:         {windows['passenger_window']}
Заднее окно водителя:   {windows['driver_rear_window']}
Заднее окно пассажира:  {windows['passenger_rear_window']}
Люк крыши:              {'🔓 Открыт' if windows['sunroof_open'] else '🔐 Закрыт'} | Позиция: {windows['sunroof_position']}%
Напоминание о закрытии: {windows['window_close_reminder']}

🛞 ШИНЫ (Давление в кПа / Температура в °C)
{'-' * 80}
Передняя левая:         {tires['driver_tire']:.1f} кПа / {tires['driver_temp']:.1f}°C
Передняя правая:        {tires['passenger_tire']:.1f} кПа / {tires['passenger_temp']:.1f}°C
Задняя левая:           {tires['driver_rear_tire']:.1f} кПа / {tires['driver_rear_temp']:.1f}°C
Задняя правая:          {tires['passenger_rear_tire']:.1f} кПа / {tires['passenger_rear_temp']:.1f}°C

🔧 ТЕХНИЧЕСКОЕ ОБСЛУЖИВАНИЕ
{'-' * 80}
Одометр:                {maintenance['odometer']:.0f} км
Дней до ТО:             {maintenance['days_to_service']} дней
Км до ТО:               {maintenance['distance_to_service']} км
Часов до ТО:            {maintenance['engine_hours_to_service']} часов
Предупреждение ТО:      {'🚨 ДА' if maintenance['service_warning_status'] else 'Нет'}
Тормозная жидкость:     {maintenance['brake_fluid_level']}
Жидкость омывателя:     {maintenance['washer_fluid_level']}
Охлаждающая жидкость:   {maintenance['engine_coolant_level']}

🚙 ДВИЖЕНИЕ
{'-' * 80}
Текущая скорость:       {movement['speed']:.1f} км/ч
Скорость валидна:       {'Да ✅' if movement['speed_valid'] else 'Нет ❌'}
Средняя скорость:       {movement['avg_speed']} км/ч
Одометр 1:              {movement['trip_meter_1']:.1f} км
Одометр 2:              {movement['trip_meter_2']:.1f} км
Направление:            {movement['direction']}°

💡 ОГНИ
{'-' * 80}
Дальний свет:           {'Включен ✅' if lights['hi_beam'] else 'Выключен ❌'}
Ближний свет:           {'Включен ✅' if lights['lo_beam'] else 'Выключен ❌'}
Дневные ходовые огни:   {'Включены ✅' if lights['drl'] else 'Выключены ❌'}
Передние противотуман:  {'Включены ✅' if lights['front_fog'] else 'Выключены ❌'}
Задние противотуман:    {'Включены ✅' if lights['rear_fog'] else 'Выключены ❌'}
Стоп-сигналы:           {'Включены ✅' if lights['stop_lights'] else 'Выключены ❌'}
Фонари заднего хода:    {'Включены ✅' if lights['reverse_lights'] else 'Выключены ❌'}

🅿️  ПАРКОВКА
{'-' * 80}
Припаркован:            {'Да ✅' if park['is_parked'] else 'Нет ❌'}
Припаркован с:          {park['parked_since'] or 'N/A'}
Время парковки:         {park['park_duration']}

💨 КАЧЕСТВО ВОЗДУХА
{'-' * 80}
PM2.5 внутри:           {pollution['interior_pm25']} мкг/м³ ({pollution['interior_pm25_level']})
PM2.5 снаружи:          {pollution['exterior_pm25_level']}
Относительная влажность: {pollution['relative_humidity']}%

{'=' * 80}
"""
        return report