# storage.py
"""
Управление сохранением и загрузкой токенов
"""
import json
import os
from typing import Optional, Dict
from config import TOKENS_FILE


class TokenStorage:
    """Класс для работы с хранилищем токенов"""

    def __init__(self, filename: str = TOKENS_FILE):
        self.filename = filename

    def save_tokens(self, tokens: Dict[str, str]) -> None:
        """
        Сохраняет токены в JSON файл

        Args:
            tokens: Словарь с ключами:
                   - jwtToken: JWT токен для TOC API
                   - accessToken: Access токен для SECURE API
                   - refreshToken: Refresh токен
                   - userId: ID пользователя
                   - clientId: Client ID
        """
        try:
            with open(self.filename, 'w') as f:
                json.dump(tokens, f, indent=4)
            print(f"✅ Токены сохранены в {self.filename}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении токенов: {e}")

    def load_tokens(self) -> Optional[Dict[str, str]]:
        """
        Загружает токены из JSON файла

        Returns:
            Словарь с токенами или None если файла нет
        """
        if not os.path.exists(self.filename):
            print(f"⚠️  Файл {self.filename} не найден")
            return None

        try:
            with open(self.filename, 'r') as f:
                tokens = json.load(f)
            print(f"✅ Токены загружены из {self.filename}")
            return tokens
        except Exception as e:
            print(f"❌ Ошибка при загрузке токенов: {e}")
            return None

    def clear_tokens(self) -> None:
        """Удаляет файл с токенами"""
        if os.path.exists(self.filename):
            os.remove(self.filename)
            print(f"✅ Токены удалены")


# Создаем глобальный экземпляр
token_storage = TokenStorage()