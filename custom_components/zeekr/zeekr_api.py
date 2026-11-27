# zeekr_api.py
"""
Работа с Zeekr API для получения данных об автомобилях
"""
import requests
import json
import uuid
import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from urllib.parse import urlencode
from .zeekr_config import (
    BASE_URL_SECURE, HMAC_SECRET, APP_VERSION, PHONE_MODEL,
    PHONE_VERSION, REQUEST_TIMEOUT
)
from .zeekr_storage import token_storage

_LOGGER = logging.getLogger(__name__)


class ZeekrAPI:
    """Класс для работы с Zeekr API (SECURE endpoint)"""

    def __init__(self, access_token: str, user_id: str, client_id: str, device_id: str):
        """
        Инициализация API клиента

        Args:
            access_token: Access токен для авторизации
            user_id: ID пользователя
            client_id: Client ID
            device_id: Device ID
        """
        self.access_token = access_token
        self.user_id = user_id
        self.client_id = client_id
        self.device_id = device_id
        self.base_url = BASE_URL_SECURE
        self.session = requests.Session()

    def _calculate_signature(self, method: str, path: str, timestamp: str,
                             nonce: str, body: str = '', query_string: str = '') -> str:
        """
        Рассчитывает подпись для SECURE API запроса

        Args:
            method: HTTP метод (GET, POST, PUT и т.д.)
            path: Путь к endpoint (например /remote-control/vehicle/status/VIN)
            timestamp: Текущее время в миллисекундах
            nonce: Уникальный UUID
            body: Тело запроса (JSON строка)
            query_string: Query параметры (отсортированные)

        Returns:
            Base64 кодированная подпись HMAC-SHA1
        """
        # Вычисляем MD5 хеш тела запроса (Base64 кодированный)
        if body:
            body_md5 = base64.b64encode(
                hashlib.md5(body.encode()).digest()
            ).decode()
        else:
            body_md5 = base64.b64encode(
                hashlib.md5(b'').digest()
            ).decode()

        # Строим строку для подписи в определенном порядке
        # Это очень важный порядок!
        string_to_sign = '\n'.join([
            'application/json;responseformat=3',
            f'x-api-signature-nonce:{nonce}',
            'x-api-signature-version:1.0',
            '',
            query_string,
            body_md5,
            timestamp,
            method.upper(),
            path,
        ])

        _LOGGER.debug("[api] canonical string сформирован")

        # Подписываем HMAC-SHA1
        signature = base64.b64encode(
            hmac.new(
                HMAC_SECRET.encode(),
                string_to_sign.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        return signature

    def _get_headers(self, method: str, path: str, timestamp: str,
                     nonce: str, body: str = '', query_string: str = '') -> Dict[str, str]:
        """
        Подготавливает заголовки для SECURE API запроса

        Args:
            method: HTTP метод
            path: Путь к endpoint
            timestamp: Текущее время в миллисекундах
            nonce: Уникальный UUID
            body: Тело запроса
            query_string: Query параметры

        Returns:
            Словарь с заголовками
        """
        signature = self._calculate_signature(
            method, path, timestamp, nonce, body, query_string
        )

        return {
            'content-type': 'application/json',
            'x-api-signature-version': '1.0',
            'x-app-id': 'ZEEKRAPP',
            'user-agent': f'ZeekrLife/{APP_VERSION} (iPhone; iOS {PHONE_VERSION}; Scale/3.00)',
            'x-device-model': 'iPhone',
            'x-device-manufacture': 'Apple',
            'x-agent-type': 'iOS',
            'x-device-type': 'mobile',
            'platform': 'NON-CMA',
            'x-env-type': 'production',
            'accept-language': 'zh-Hans-CN;q=1, en-CN;q=0.9',
            'x-agent-version': PHONE_VERSION,
            'accept': 'application/json;responseformat=3',
            'x-device-brand': 'Apple',
            'x-operator-code': 'ZEEKR',
            'x-device-identifier': self.device_id,
            'authorization': self.access_token,
            'x-client-id': self.client_id,
            'x-timestamp': timestamp,
            'x-api-signature-nonce': nonce,
            'x-signature': signature,
        }

    def get_vehicles(self) -> Tuple[bool, Optional[List[str]]]:
        """
        Получает список VIN номеров автомобилей пользователя

        Returns:
            Кортеж (успешность, список VIN или None)
        """
        _LOGGER.debug("Запрашиваю список автомобилей")

        timestamp = str(int(datetime.now().timestamp() * 1000))
        nonce = str(uuid.uuid4()).upper()

        path = '/device-platform/user/vehicle/secure'
        params = {
            'id': self.user_id,
            'needSharedCar': '1'
        }

        # Сортируем параметры и создаем query string
        query_string = urlencode(sorted(params.items()))

        url = f"{self.base_url}{path}?{query_string}"

        try:
            response = self.session.get(
                url,
                headers=self._get_headers('GET', path, timestamp, nonce, '', query_string),
                timeout=REQUEST_TIMEOUT
            )

            data = response.json()

            if data.get('code') == '1000':
                vehicles = [v['vin'] for v in data.get('data', {}).get('list', [])]
                _LOGGER.debug("Найдено %s автомобилей", len(vehicles))
                return True, vehicles
            else:
                error_msg = data.get('message', 'Неизвестная ошибка')
                _LOGGER.error("Ошибка получения списка автомобилей: %s", error_msg)
                return False, None

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Ошибка HTTP-запроса: %s", e)
            return False, None

    def get_vehicle_status(self, vin: str) -> Tuple[bool, Optional[Dict]]:
        """
        Получает статус конкретного автомобиля

        Args:
            vin: VIN номер автомобиля

        Returns:
            Кортеж (успешность, словарь со статусом или None)
        """
        _LOGGER.debug("Запрашиваю статус автомобиля")

        timestamp = str(int(datetime.now().timestamp() * 1000))
        nonce = str(uuid.uuid4()).upper()

        path = f'/remote-control/vehicle/status/{vin}'
        params = {
            'latest': 'Local',
            'target': 'basic,more',
            'userId': self.user_id,
        }

        # Сортируем параметры и создаем query string
        query_string = urlencode(sorted(params.items()))

        url = f"{self.base_url}{path}?{query_string}"

        try:
            response = self.session.get(
                url,
                headers=self._get_headers('GET', path, timestamp, nonce, '', query_string),
                timeout=REQUEST_TIMEOUT
            )

            data = response.json()

            if data.get('code') == '1000':
                vehicle_status = data.get('data', {}).get('vehicleStatus', {})
                _LOGGER.debug("Статус автомобиля получен")
                return True, vehicle_status
            else:
                error_msg = data.get('message', 'Неизвестная ошибка')
                _LOGGER.error("Ошибка получения статуса: %s (код: %s)", error_msg, data.get("code"))
                return False, None

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Ошибка HTTP-запроса: %s", e)
            return False, None

    def get_all_vehicles_status(self) -> Tuple[bool, Optional[Dict[str, Dict]]]:
        """
        Получает статус всех автомобилей пользователя

        Returns:
            Кортеж (успешность, словарь {VIN: статус} или None)
        """
        _LOGGER.debug("Получение статуса всех автомобилей")

        # Сначала получаем список VIN
        success, vehicles = self.get_vehicles()
        if not success or not vehicles:
            return False, None

        # Затем получаем статус каждого
        all_status = {}
        for vin in vehicles:
            success, status = self.get_vehicle_status(vin)
            if success and status:
                all_status[vin] = status

        return True, all_status if all_status else None