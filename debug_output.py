# debug_output.py
"""
Вывод полной структуры данных для отладки
"""
import json
from zeekr_api import ZeekrAPI
from storage import token_storage


def print_all_vehicle_data():
    """Выводит всю структуру данных автомобиля"""

    # Загружаем токены
    tokens = token_storage.load_tokens()
    if not tokens:
        print("❌ Токены не найдены")
        return

    # Инициализируем API
    api = ZeekrAPI(
        access_token=tokens.get('accessToken'),
        user_id=tokens.get('userId'),
        client_id=tokens.get('clientId'),
        device_id=tokens.get('device_id')
    )

    # Получаем список автомобилей
    print("\n" + "=" * 80)
    print("🚗 ПОЛУЧЕНИЕ СПИСКА АВТОМОБИЛЕЙ")
    print("=" * 80)

    success, vehicles = api.get_vehicles()
    if not success:
        print("❌ Ошибка при получении списка")
        return

    # Для каждого автомобиля получаем статус
    for vin in vehicles:
        print("\n" + "=" * 80)
        print(f"🚗 ПОЛНЫЕ ДАННЫЕ АВТОМОБИЛЯ: {vin}")
        print("=" * 80)

        success, status = api.get_vehicle_status(vin)
        if success:
            # Выводим весь JSON в красивом формате
            json_output = json.dumps(status, indent=2, ensure_ascii=False)
            print(json_output)

            # Также сохраняем в файл
            filename = f"vehicle_data_{vin}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)

            print(f"\n✅ Данные сохранены в файл: {filename}")
        else:
            print("❌ Ошибка при получении статуса")


def print_structure_analysis():
    """Анализирует и выводит структуру данных"""

    tokens = token_storage.load_tokens()
    if not tokens:
        print("❌ Токены не найдены")
        return

    api = ZeekrAPI(
        access_token=tokens.get('accessToken'),
        user_id=tokens.get('userId'),
        client_id=tokens.get('clientId'),
        device_id=tokens.get('device_id')
    )

    success, vehicles = api.get_vehicles()
    if not success:
        return

    vin = vehicles[0]
    success, status = api.get_vehicle_status(vin)

    if not success:
        return

    print("\n" + "=" * 80)
    print("📊 АНАЛИЗ СТРУКТУРЫ ДАННЫХ")
    print("=" * 80)

    def analyze_dict(d, prefix="", level=0):
        """Рекурсивно анализирует словарь и выводит его структуру"""
        indent = "  " * level

        for key, value in d.items():
            if isinstance(value, dict):
                print(f"{indent}📁 {key}:")
                analyze_dict(value, prefix + key + ".", level + 1)
            elif isinstance(value, list):
                print(f"{indent}📋 {key}: [список из {len(value)} элементов]")
                if value and isinstance(value[0], dict):
                    print(f"{indent}   Пример первого элемента:")
                    analyze_dict(value[0], prefix + key + "[0].", level + 2)
            else:
                print(f"{indent}📌 {key}: {type(value).__name__} = {str(value)[:60]}")

    analyze_dict(status)


if __name__ == '__main__':
    print("\n🔍 ВЫБЕРИ РЕЖИМ:")
    print("1. Вывести полные данные (JSON)")
    print("2. Вывести структуру данных (анализ)")
    print("3. Оба варианта")

    choice = input("\nВведите номер (1-3): ").strip()

    if choice == '1':
        print_all_vehicle_data()
    elif choice == '2':
        print_structure_analysis()
    elif choice == '3':
        print_structure_analysis()
        print("\n\n")
        print_all_vehicle_data()
    else:
        print("❌ Неверный выбор")