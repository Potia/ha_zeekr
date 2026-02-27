# custom_components/zeekr/zeekr_storage.py
"""
Управление сохранением и загрузкой токенов

ОСНОВНОЕ ХРАНИЛИЩЕ: entry.data в Home Assistant
РЕЗЕРВНОЕ ХРАНИЛИЩЕ: tokens.json файл
"""
import json
import os
from typing import Optional, Dict

_LOGGER = None


def set_logger(logger):
    """Устанавливает логгер"""
    global _LOGGER
    _LOGGER = logger


class TokenStorage:
    """Класс для работы с хранилищем токенов"""

    def __init__(self):
        """Инициализация хранилища"""
        # Получаем папку где находится этот файл
        self.storage_dir = os.path.dirname(os.path.abspath(__file__))
        self.filename = os.path.join(self.storage_dir, 'tokens.json')

    def save_tokens(self, tokens: Dict[str, str]) -> None:
        """
        Сохраняет токены в JSON файл (РЕЗЕРВНОЕ ХРАНИЛИЩЕ)

        Основное хранилище: entry.data в Home Assistant
        Это РЕЗЕРВНАЯ копия для миграции старых установок

        Args:
            tokens: Словарь с ключами:
                   - accessToken: Access токен для SECURE API
                   - refreshToken: Refresh токен
                   - userId: ID пользователя
                   - clientId: Client ID
                   - device_id: Device ID
        """
        try:
            if _LOGGER:
                _LOGGER.debug(f"[TokenStorage] Saving tokens (backup) to {self.filename}")

            with open(self.filename, 'w') as f:
                json.dump(tokens, f, indent=4)

            if _LOGGER:
                _LOGGER.info(f"✅ [TokenStorage] Tokens saved (backup)")
        except Exception as e:
            if _LOGGER:
                _LOGGER.error(f"❌ [TokenStorage] Failed to save tokens: {e}")

    def load_tokens(self) -> Optional[Dict[str, str]]:
        """
        Загружает токены из JSON файла (РЕЗЕРВНОЕ ХРАНИЛИЩЕ)

        Используется для миграции со старых версий

        Returns:
            Словарь с токенами или None если файла нет
        """
        if not os.path.exists(self.filename):
            if _LOGGER:
                _LOGGER.debug(f"[TokenStorage] File {self.filename} not found")
            return None

        try:
            with open(self.filename, 'r') as f:
                tokens = json.load(f)

            if _LOGGER:
                _LOGGER.info(f"✅ [TokenStorage] Tokens loaded from file (backup)")

            return tokens
        except Exception as e:
            if _LOGGER:
                _LOGGER.error(f"❌ [TokenStorage] Failed to load tokens: {e}")
            return None

    def clear_tokens(self) -> None:
        """Удаляет файл с токенами"""
        if os.path.exists(self.filename):
            os.remove(self.filename)
            if _LOGGER:
                _LOGGER.info(f"✅ [TokenStorage] Tokens file deleted")


# Создаем глобальный экземпляр
token_storage = TokenStorage()