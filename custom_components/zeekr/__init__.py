# custom_components/zeekr/__init__.py
"""Zeekr integration for Home Assistant"""

import logging
import sys
import os
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zeekr integration"""

    _LOGGER.debug("Setting up Zeekr integration")

    try:
        # Добавляем родительскую папку в sys.path для импорта
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Импортируем необходимые модули
        from zeekr_api import ZeekrAPI
        from storage import token_storage
        from coordinator import ZeekrDataCoordinator

        # Загружаем токены
        tokens = token_storage.load_tokens()

        if not tokens:
            _LOGGER.error("No tokens found, cannot setup Zeekr integration")
            return False

        # Проверяем необходимые поля
        required_fields = ['accessToken', 'userId', 'clientId', 'device_id']
        for field in required_fields:
            if field not in tokens:
                _LOGGER.error(f"Missing required token field: {field}")
                return False

        # Создаем API клиент
        api_client = ZeekrAPI(
            access_token=tokens.get('accessToken'),
            user_id=tokens.get('userId'),
            client_id=tokens.get('clientId'),
            device_id=tokens.get('device_id')
        )

        # Создаем coordinator
        coordinator = ZeekrDataCoordinator(hass, api_client)

        # Получаем первые данные
        await coordinator.async_config_entry_first_refresh()

        # Сохраняем coordinator в hass.data
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        # Устанавливаем platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info("Zeekr integration setup successfully")

        return True

    except Exception as err:
        _LOGGER.error(f"Error setting up Zeekr integration: {err}", exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Zeekr integration"""

    _LOGGER.debug("Unloading Zeekr integration")

    try:
        # Выгружаем все platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)

        return unload_ok

    except Exception as err:
        _LOGGER.error(f"Error unloading Zeekr integration: {err}")
        return False