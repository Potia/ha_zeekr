# storage.py
"""
Управление сохранением и загрузкой токенов
"""
import json
import os
from typing import Optional, Dict
from .zeekr_config import TOKENS_FILE

class TokenStorage:
    """Класс для работы с хранилищем токенов"""

    def __init__(self):
        """Инициализация хранилища"""
        # Получаем папку где находится этот файл
        self.storage_dir = os.path.dirname(os.path.abspath(__file__))
        self.filename = os.path.join(self.storage_dir, 'tokens.json')
        print(f"[TokenStorage] Токены будут сохранены в: {self.filename}")

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
            print(f"[TokenStorage] Сохраняю токены в {self.filename}")
            with open(self.filename, 'w') as f:
                json.dump(tokens, f, indent=4)
            print(f"✅ [TokenStorage] Токены сохранены успешно")
        except Exception as e:
            print(f"❌ [TokenStorage] Ошибка при сохранении токенов: {e}")
            import traceback
            traceback.print_exc()

    def load_tokens(self) -> Optional[Dict[str, str]]:
        """
        Загружает токены из JSON файла

        Returns:
            Словарь с токенами или None если файла нет
        """
        if not os.path.exists(self.filename):
            print(f"⚠️  [TokenStorage] Файл {self.filename} не найден")
            return None

        try:
            with open(self.filename, 'r') as f:
                tokens = json.load(f)
            print(f"✅ [TokenStorage] Токены загружены из {self.filename}")
            return tokens
        except Exception as e:
            print(f"❌ [TokenStorage] Ошибка при загрузке токенов: {e}")
            return None

    def clear_tokens(self) -> None:
        """Удаляет файл с токенами"""
        if os.path.exists(self.filename):
            os.remove(self.filename)
            print(f"✅ [TokenStorage] Токены удалены")


# Создаем глобальный экземпляр
token_storage = TokenStorage()