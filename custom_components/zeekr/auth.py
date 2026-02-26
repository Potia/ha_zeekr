# auth.py
"""
Аутентификация в Zeekr API
"""
import hmac
import base64
import requests
import json
import uuid
import hashlib
import random
from typing import Optional, Dict, Tuple
from datetime import datetime
from .zeekr_config import (
    BASE_URL_TOC, X_CA_SECRET, X_CA_KEY, APP_VERSION,
    PHONE_MODEL, PHONE_VERSION, APP_TYPE, REQUEST_TIMEOUT,
    REGION_CODE, BASE_URL_SECURE, HMAC_SECRET
)
from storage import token_storage


class ZeekrAuth:
    """Класс для аутентификации в Zeekr"""

    def __init__(self):
        self.device_id = str(uuid.uuid4())
        self.base_url = BASE_URL_TOC
        self.session = requests.Session()
        self.mobile = None  # Сохраняем мобильный номер

    def _generate_signature(self, timestamp: str, nonce: int) -> str:
        """
        Генерирует подпись для API запроса (TOC)

        Args:
            timestamp: Текущее время в миллисекундах
            nonce: Случайное число

        Returns:
            SHA1 хеш подписи
        """
        # Сортируем компоненты подписи
        arr = [timestamp, str(nonce), X_CA_SECRET]
        arr.sort()

        # Объединяем в одну строку
        combined_str = ''.join(arr)

        # Создаем SHA1 хеш
        sha1_hash = hashlib.sha1(combined_str.encode()).hexdigest()
        return sha1_hash

    def _get_headers(self, timestamp: str, nonce: int) -> Dict[str, str]:
        """
        Подготавливает заголовки для запроса

        Args:
            timestamp: Текущее время в миллисекундах
            nonce: Случайное число

        Returns:
            Словарь с заголовками
        """
        return {
            'User-Agent': f'ZeekrLife/{APP_VERSION} (iPhone; iOS {PHONE_VERSION}; Scale/3.00){self.device_id}',
            'request-original': 'zeekr-app',
            'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9',
            'Content-Type': 'application/json',
            'x_ca_secret': X_CA_SECRET,
            'Accept': '*/*',
            'riskToken': 'G4y5f5YrG1BEGxRBBEKF73higM/lOd6e',
            'Version': '2',
            'WorkspaceId': 'prod',
            'x_ca_key': X_CA_KEY,
            'app_type': APP_TYPE,
            'app_version': APP_VERSION,
            'phone_model': PHONE_MODEL,
            'phone_version': PHONE_VERSION,
            'x_gray_code': 'gray74',
            'x_ca_timestamp': timestamp,
            'x_ca_nonce': str(nonce),
            'x_ca_sign': self._generate_signature(timestamp, nonce),
            'app_code': 'toc_ios_zeekrapp',
            'device_id': self.device_id,
        }

    def request_sms_code(self, mobile: str) -> Tuple[bool, str]:
        """
        Запрашивает SMS код для входа

        Args:
            mobile: Номер телефона в формате "13812345678"

        Returns:
            Кортеж (успешность, сообщение)
        """
        print(f"\n📱 Запрашиваю SMS код на номер {mobile}...")

        timestamp = str(int(datetime.now().timestamp() * 1000))
        nonce = int(random.random() * 1e8)

        url = f"{self.base_url}/zeekrlife-app-user/v1/user/pub/sms/authCode"
        params = {
            'mobile': mobile,
            'x_ca_time': timestamp,
            'regionCode': REGION_CODE,
        }

        try:
            response = self.session.get(
                url,
                params=params,
                headers=self._get_headers(timestamp, nonce),
                timeout=REQUEST_TIMEOUT
            )

            data = response.json()

            if data.get('code') == '000000':
                print("✅ SMS код отправлен!")
                return True, "SMS код отправлен успешно"
            else:
                error_msg = data.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка: {error_msg}")
                return False, error_msg

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при отправке запроса: {e}")
            return False, str(e)

    def login_with_sms(self, mobile: str, sms_code: str) -> Tuple[bool, Optional[Dict]]:
        """
        Авторизация по SMS коду (ШАГ 1)

        Args:
            mobile: Номер телефона
            sms_code: SMS код из сообщения

        Returns:
            Кортеж (успешность, словарь с токенами или None)
        """
        print(f"\n🔐 Пытаюсь авторизоваться с SMS кодом...")

        timestamp = str(int(datetime.now().timestamp() * 1000))
        nonce = int(random.random() * 1e8)

        url = f"{self.base_url}/zeekrlife-app-user/v1/user/pub/login/mobile"

        payload = {
            'mobile': mobile,
            'deviceId': self.device_id,
            'smsCode': sms_code,
            'channel': 2,
            'x_ca_time': timestamp,
            'deviceName': PHONE_MODEL,
            'skipSmsCode': '0',
            'regionCode': REGION_CODE,
            'ip': '192.168.1.1',
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(timestamp, nonce),
                timeout=REQUEST_TIMEOUT
            )

            data = response.json()

            if data.get('code') == '000000':
                tokens = {
                    'jwtToken': data.get('data', {}).get('jwtToken'),
                    'mobile': mobile,
                    'device_id': self.device_id,
                }
                self.mobile = mobile  # Сохраняем мобильный
                print("✅ Авторизация успешна!")
                return True, tokens
            else:
                error_msg = data.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка авторизации: {error_msg}")
                return False, None

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе: {e}")
            return False, None

    def get_auth_code(self, jwt_token: str) -> Tuple[bool, Optional[str]]:
        """
        Получает Auth Code (YIKAT_NEW) используя JWT токен (ШАГ 2)

        Args:
            jwt_token: JWT токен из login_with_sms

        Returns:
            Кортеж (успешность, Auth Code или None)
        """
        print(f"\n🔑 Получаю Auth Code...")

        timestamp = str(int(datetime.now().timestamp() * 1000))
        nonce = int(random.random() * 1e8)

        url = f"{self.base_url}/zeekrlife-mp-auth2/v1/auth/accessCodeList"
        params = {
            'envType': '3',
        }

        # Подготавливаем заголовки с JWT токеном
        headers = self._get_headers(timestamp, nonce)
        headers['Authorization'] = jwt_token

        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            data = response.json()

            if data.get('code') == '000000':
                auth_code = data.get('data', {}).get('YIKAT_NEW')
                if auth_code:
                    print(f"✅ Auth Code получен: {auth_code[:20]}...")
                    return True, auth_code
                else:
                    print("❌ Auth Code не найден в ответе")
                    return False, None
            else:
                error_msg = data.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка получения Auth Code: {error_msg}")
                return False, None

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе: {e}")
            return False, None

    def login_with_auth_code(self, auth_code: str) -> Tuple[bool, Optional[Dict]]:
        """
        Авторизация с использованием Auth Code (ШАГ 3)
        Получает accessToken, refreshToken, userId и clientId

        Args:
            auth_code: Auth Code полученный из get_auth_code

        Returns:
            Кортеж (успешность, словарь с полными токенами или None)
        """
        print(f"\n🔐 Авторизуюсь с Auth Code...")

        import hmac
        import base64
        from urllib.parse import urlencode

        timestamp = str(int(datetime.now().timestamp() * 1000))
        nonce = str(uuid.uuid4()).upper()

        # Используем BASE_URL_SECURE для этого запроса
        url = f"{BASE_URL_SECURE}/auth/account/session/secure"

        params = {
            'identity_type': 'zeekr',
        }

        payload = {
            'authCode': auth_code,
        }

        # ========== ВЫЧИСЛЯЕМ ПОДПИСЬ ==========
        # Сортируем параметры
        query_string = urlencode(sorted(params.items()))

        # JSON payload
        body = json.dumps(payload)

        # MD5 хеш тела (Base64)
        body_md5 = base64.b64encode(
            hashlib.md5(body.encode()).digest()
        ).decode()

        # Строим строку для подписи
        string_to_sign = '\n'.join([
            'application/json;responseformat=3',
            f'x-api-signature-nonce:{nonce}',
            'x-api-signature-version:1.0',
            '',
            query_string,
            body_md5,
            timestamp,
            'POST',
            '/auth/account/session/secure',
        ])

        print(f"[DEBUG] String to sign:\n{string_to_sign}\n")

        # Подписываем HMAC-SHA1
        signature = base64.b64encode(
            hmac.new(
                HMAC_SECRET.encode(),
                string_to_sign.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        print(f"[DEBUG] Signature: {signature}\n")

        # Готовим заголовки как для SECURE API с подписью
        headers = {
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
            'x-timestamp': timestamp,
            'x-api-signature-nonce': nonce,
            'x-signature': signature,
        }

        try:
            # Построим URL с параметрами
            full_url = f"{url}?{query_string}"

            print(f"[DEBUG] Full URL: {full_url}")
            print(f"[DEBUG] Body: {body}")

            response = self.session.post(
                full_url,
                data=body,  # Используем data вместо json для контроля над JSON
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            print(f"[DEBUG] Response status: {response.status_code}")

            data = response.json()
            print(f"[DEBUG] Ответ от auth/account/session/secure: {json.dumps(data, indent=2, ensure_ascii=False)}")

            if data.get('code') == 1000 or str(data.get('code')) == '1000':
                session_data = data.get('data', {})
                tokens = {
                    'jwtToken': '',  # Будет добавлено ниже
                    'accessToken': session_data.get('accessToken'),
                    'refreshToken': session_data.get('refreshToken'),
                    'userId': session_data.get('userId'),
                    'clientId': session_data.get('clientId'),
                    'mobile': self.mobile if self.mobile else '',
                    'device_id': self.device_id,
                }
                print("✅ Авторизация с Auth Code успешна!")
                return True, tokens
            else:
                error_msg = data.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка авторизации с Auth Code: {error_msg}")
                return False, None

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе: {e}")
            return False, None