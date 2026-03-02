SENSOR_GROUPS = {
    "🔋 Батарея": [
        "battery",
        "battery_12v_percentage",
        "battery_12v_voltage",
        "distance_to_empty",
        "state_of_charge",
        "state_of_health",
        "hv_temp_level",
        "time_to_full_charge",
    ],

    "🌡️ Температура": [
        "interior_temp",
        "exterior_temp",
        "hv_temp_level",
        "tire_temp_driver_front",
        "tire_temp_passenger_front",
        "tire_temp_driver_rear",
        "tire_temp_passenger_rear",
    ],

    "🛞 Шины": [
        "tire_pressure_driver",
        "tire_pressure_passenger",
        "tire_pressure_driver_rear",
        "tire_pressure_passenger_rear",
        "tire_temp_driver_front",
        "tire_temp_passenger_front",
        "tire_temp_driver_rear",
        "tire_temp_passenger_rear",
    ],

    "🚙 Движение": [
        "current_speed",
        "average_speed",
        "speed",
        "brake_status",
        "gear_status",
        "energy_recovery",
        "trip_meter_1",
        "trip_meter_2",
    ],

    "🔧 Обслуживание": [
        "odometer",
        "days_to_service",
        "distance_to_service",
        "engine_hours_to_service",
        "brake_fluid_level",
        "washer_fluid_level",
        "engine_coolant_level",
    ],

    "⚡ Зарядка": [
        "dc_charge_power",
        "dc_charge_voltage_detailed",
        "dc_charge_current_detailed",
        "dc_charge_status_detailed",
        "dcdc_status",
        "time_to_full_charge",
    ],

    "⚡ Разрядка": [
        "discharge_power",
        "discharge_voltage",
        "discharge_current",
        "charger_state",
    ],

    "☀️ Панорамная Крыша": [
        "front_shade_position",
        "rear_shade_position",
        "roof_status",
    ],

    "🔒 Безопасность": [
        "seatbelt_driver",
        "seatbelt_passenger",
        "seatbelt_status",
    ],

    "📍 Местоположение": [
        "latitude",
        "longitude",
        "altitude",
        "gps_status",
    ],

    "💡 Огни": [
        "lights_status",
    ],

    "💨 Воздух": [
        "pm25_interior",
        "exterior_pm25_level",
        "relative_humidity",
    ],

    "🅿️ Парковка": [
        "park_duration",
    ],

    "🎯 Климат": [
        "interior_temp",
        "exterior_temp",
        "steering_wheel_heating",
        "driver_heating",
        "passenger_heating",
    ],

    "🚗 Статус": [
        "last_update_time",
        "battery",
        "theft_protection",
        "electric_park_brake",
    ],
}


def get_group_entities_for_vin(vin: str, group_name: str) -> list:
    """
    Получает список entity_id для группы и VIN

    Args:
        vin: VIN автомобиля
        group_name: Название группы

    Returns:
        Список entity_id
    """
    if group_name not in SENSOR_GROUPS:
        return []

    entities = []
    vin_lower = vin.lower()

    for sensor_type in SENSOR_GROUPS[group_name]:
        entity_id = f"sensor.zeekr_{vin_lower}_{sensor_type}"
        entities.append(entity_id)

    return entities