# config.py
"""
Конфигурация для Zeekr API интеграции
"""

# ==================== API ENDPOINTS ====================
BASE_URL_TOC = 'https://api-gw-toc.zeekrlife.com'  # Для аутентификации
BASE_URL_SECURE = 'https://api.zeekrline.com'      # Для получения данных об авто
YIKAT_AUTH_ENDPOINT = '/zeekrlife-mp-auth2/v1/auth/accessCodeList' # Для получения YIKAT

# ==================== API KEYS ====================
X_CA_SECRET = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCz09z6e9WOcNq+nUMX8Vq1Xe2EmJxuR3XbtureDCS90dfkok'
X_CA_KEY = 'APP-SIGN-SECRET-KEY'
HMAC_SECRET = 'e83a60805fa54de9bdfcb0f2d6bca757'

# ==================== APP INFO ====================
APP_VERSION = '4.0.2'
PHONE_MODEL = 'iPhone13'
PHONE_VERSION = '17.4.1'
APP_TYPE = 'IOS'

# ==================== REQUEST SETTINGS ====================
REQUEST_TIMEOUT = 30  # Таймаут для запросов в секундах
REFRESH_INTERVAL = 5  # Интервал обновления статуса в минутах
MAX_RETRIES = 3       # Максимум попыток переподключения

# ==================== STORAGE ====================
TOKENS_FILE = 'tokens.json'  # Файл для сохранения токенов

# ==================== REGION ====================
REGION_CODE = '+86'  # Китайский регион