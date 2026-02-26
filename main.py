# main.py
"""
Главный файл приложения Zeekr для Home Assistant
"""
import json
from typing import Optional, Dict
from auth import ZeekrAuth
from zeekr_api import ZeekrAPI
from storage import token_storage
from scheduler import create_scheduler
from config import REFRESH_INTERVAL


class ZeekrManager:
    """Главный менеджер для управления Zeekr интеграцией"""

    def __init__(self):
        self.auth: Optional[ZeekrAuth] = None
        self.api: Optional[ZeekrAPI] = None
        self.tokens: Optional[Dict] = None
        self.scheduler = None
        self.vehicle_status_cache = {}

    def full_authorization(self, mobile: str, sms_code: str) -> bool:
        """
        Полная авторизация (все 3 шага):
        1. SMS логин → получение jwtToken
        2. Получение Auth Code
        3. Логин с Auth Code → получение accessToken и refreshToken

        Args:
            mobile: Номер телефона
            sms_code: SMS код

        Returns:
            True если успешно, False если ошибка
        """
        print("\n" + "=" * 50)
        print("🔐 ПОЛНАЯ АВТОРИЗАЦИЯ (3 ШАГА)")
        print("=" * 50)

        # Создаем объект аутентификации
        self.auth = ZeekrAuth()

        # ========== ШАГ 1: SMS логин ==========
        print("\n[ШАГ 1/3] SMS логин...")
        success, toc_tokens = self.auth.login_with_sms(mobile, sms_code)
        if not success:
            print("❌ Ошибка на шаге 1 (SMS логин)")
            return False

        jwt_token = toc_tokens['jwtToken']
        self.auth.mobile = mobile  # Сохраняем мобильный

        # ========== ШАГ 2: Получение Auth Code ==========
        print("\n[ШАГ 2/3] Получение Auth Code...")
        success, auth_code = self.auth.get_auth_code(jwt_token)
        if not success:
            print("❌ Ошибка на шаге 2 (получение Auth Code)")
            return False

        # ========== ШАГ 3: Логин с Auth Code ==========
        print("\n[ШАГ 3/3] Логин с Auth Code...")
        success, secure_tokens = self.auth.login_with_auth_code(auth_code)
        if not success:
            print("❌ Ошибка на шаге 3 (логин с Auth Code)")
            return False

        # Сохраняем полные токены
        self.tokens = secure_tokens
        token_storage.save_tokens(self.tokens)

        print("\n" + "=" * 50)
        print("✅ ПОЛНАЯ АВТОРИЗАЦИЯ УСПЕШНА")
        print("=" * 50)
        return True

    def load_saved_tokens(self) -> bool:
        """
        Загружает сохраненные токены из файла

        Returns:
            True если токены загружены, False если файла нет или ошибка
        """
        print("\n" + "=" * 50)
        print("💾 ЗАГРУЗКА СОХРАНЕННЫХ ТОКЕНОВ")
        print("=" * 50)

        tokens = token_storage.load_tokens()

        if not tokens:
            print("❌ Токены не найдены. Требуется авторизация.")
            return False

        self.tokens = tokens

        # Проверяем наличие необходимых полей для работы с SECURE API
        required_fields = ['accessToken', 'userId', 'clientId']
        for field in required_fields:
            if field not in tokens:
                print(f"❌ В токенах отсутствует поле: {field}")
                print("   Требуется переавторизация.")
                return False

        print("✅ Токены успешно загружены")
        print(f"   - User ID: {tokens.get('userId')}")
        print(f"   - Client ID: {tokens.get('clientId')}")
        return True

    def initialize_api(self) -> bool:
        """
        Инициализирует API клиент с текущими токенами

        Returns:
            True если успешно, False если ошибка
        """
        if not self.tokens:
            print("❌ Токены не установлены. Сначала авторизуйтесь.")
            return False

        try:
            self.api = ZeekrAPI(
                access_token=self.tokens.get('accessToken'),
                user_id=self.tokens.get('userId'),
                client_id=self.tokens.get('clientId'),
                device_id=self.tokens.get('device_id', 'unknown')
            )
            print("✅ API клиент инициализирован")
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации API: {e}")
            return False

    def update_vehicle_status(self) -> None:
        """
        Обновляет статус всех автомобилей (вызывается по расписанию)
        """
        if not self.api:
            print("❌ API клиент не инициализирован")
            return

        success, all_status = self.api.get_all_vehicles_status()

        if success and all_status:
            self.vehicle_status_cache = all_status
            self._print_status_summary()
        else:
            print("❌ Ошибка при получении статуса автомобилей")

    def _print_status_summary(self) -> None:
        """Выводит полную информацию о статусе всех автомобилей"""

        for vin, status in self.vehicle_status_cache.items():
            from vehicle_parser import VehicleDataParser

            # Создаем парсер для этого автомобиля
            parser = VehicleDataParser(status)

            # Выводим полный отчет
            print(parser.get_full_summary())

    def start_monitoring(self) -> None:
        """
        Запускает мониторинг статуса с заданным интервалом
        """
        print("\n" + "=" * 50)
        print("⏰ ЗАПУСК МОНИТОРИНГА")
        print("=" * 50)

        # Сначала выполняем один раз
        print("\n🔄 Первое обновление...")
        self.update_vehicle_status()

        # Создаем планировщик
        self.scheduler = create_scheduler()

        # Добавляем задачу обновления каждые 5 минут
        self.scheduler.add_job(
            REFRESH_INTERVAL,
            self.update_vehicle_status
        )

        # Запускаем планировщик (блокирующий режим)
        self.scheduler.start()

    def get_current_status(self) -> Dict:
        """
        Возвращает текущий кешированный статус

        Returns:
            Словарь со статусом всех автомобилей
        """
        return self.vehicle_status_cache


def main():
    """Главная функция"""
    print("\n" + "=" * 50)
    print("🚗 ZEEKR HOME ASSISTANT ИНТЕГРАЦИЯ")
    print("=" * 50)

    # Создаем менеджер
    manager = ZeekrManager()

    # Пытаемся загрузить сохраненные токены
    if manager.load_saved_tokens():
        # Если токены есть, инициализируем API
        if manager.initialize_api():
            # Запускаем мониторинг
            manager.start_monitoring()
        else:
            print("❌ Ошибка инициализации API")
    else:
        # Если токенов нет, нужна полная авторизация
        print("\n📱 ТРЕБУЕТСЯ ПОЛНАЯ АВТОРИЗАЦИЯ")
        print("-" * 50)

        mobile = input("Введите номер телефона (в формате 13812345678): ").strip()

        # Запрашиваем SMS код
        auth = ZeekrAuth()
        success, msg = auth.request_sms_code(mobile)

        if not success:
            print(f"❌ Ошибка: {msg}")
            return

        # Вводим SMS код
        sms_code = input("Введите SMS код: ").strip()

        # Выполняем полную авторизацию (все 3 шага)
        if manager.full_authorization(mobile, sms_code):
            # Инициализируем API
            if manager.initialize_api():
                # Запускаем мониторинг
                manager.start_monitoring()
            else:
                print("❌ Ошибка инициализации API")
        else:
            print("❌ Ошибка при полной авторизации")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback

        traceback.print_exc()