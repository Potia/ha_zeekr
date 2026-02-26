# scheduler.py
"""
Планировщик для периодического обновления статуса
"""
import schedule
import time
from typing import Callable, Optional
from config import REFRESH_INTERVAL


class ZeekrScheduler:
    """Класс для планирования задач"""

    def __init__(self):
        self.tasks = []
        self.running = False

    def add_job(self, interval_minutes: int, job_func: Callable, *args, **kwargs) -> None:
        """
        Добавляет задачу в расписание

        Args:
            interval_minutes: Интервал в минутах
            job_func: Функция для выполнения
            *args: Позиционные аргументы функции
            **kwargs: Именованные аргументы функции
        """

        def job_wrapper():
            try:
                job_func(*args, **kwargs)
            except Exception as e:
                print(f"❌ Ошибка при выполнении задачи: {e}")

        # Добавляем задачу в расписание
        schedule.every(interval_minutes).minutes.do(job_wrapper)
        self.tasks.append(job_wrapper)

        print(f"✅ Задача добавлена: будет выполняться каждые {interval_minutes} минут")

    def start(self) -> None:
        """
        Запускает планировщик (блокирующий режим)

        Примечание: Эта функция блокирует выполнение программы.
        Используйте в отдельном потоке для неблокирующего выполнения.
        """
        self.running = True
        print("\n⏰ Планировщик запущен. Нажмите Ctrl+C для остановки.")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)  # Проверяем каждую секунду
        except KeyboardInterrupt:
            print("\n⏹️  Планировщик остановлен")
            self.running = False

    def stop(self) -> None:
        """Останавливает планировщик"""
        self.running = False
        schedule.clear()
        print("✅ Планировщик очищен")

    def run_once(self) -> None:
        """Выполняет все ожидающие задачи один раз"""
        schedule.run_all()


# Функция для удобного создания планировщика
def create_scheduler() -> ZeekrScheduler:
    """Создает и возвращает новый планировщик"""
    return ZeekrScheduler()