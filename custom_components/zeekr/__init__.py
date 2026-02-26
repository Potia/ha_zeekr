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

    _LOGGER.info(f"🔧 Setting up Zeekr integration for entry {entry.entry_id}")

    try:
        # Добавляем текущую папку в sys.path
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        _LOGGER.debug(f"Current dir: {current_dir}")

        # Импортируем необходимые модули (абсолютно)
        from zeekr_api import ZeekrAPI
        from storage import token_storage

        _LOGGER.debug("Modules imported successfully")

        # Загружаем токены
        tokens = token_storage.load_tokens()

        if not tokens:
            _LOGGER.error("❌ No tokens found in storage")
            return False

        _LOGGER.info(f"✅ Tokens loaded")

        # Проверяем необходимые поля
        required_fields = ['accessToken', 'userId', 'clientId', 'device_id']
        missing_fields = [f for f in required_fields if f not in tokens or not tokens[f]]

        if missing_fields:
            _LOGGER.error(f"❌ Missing required token fields: {missing_fields}")
            return False

        _LOGGER.info("✅ All required fields present")

        # Создаем API клиент
        try:
            api_client = ZeekrAPI(
                access_token=tokens.get('accessToken'),
                user_id=tokens.get('userId'),
                client_id=tokens.get('clientId'),
                device_id=tokens.get('device_id')
            )
            _LOGGER.info("✅ API client created")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to create API client: {e}")
            return False

        # Импортируем coordinator (абсолютно, без точки)
        from coordinator import ZeekrDataCoordinator

        # Создаем coordinator
        try:
            coordinator = ZeekrDataCoordinator(hass, api_client)
            _LOGGER.info("✅ Coordinator created")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to create coordinator: {e}", exc_info=True)
            return False

        # Получаем первые данные
        try:
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.info("✅ First data refresh successful")
        except Exception as e:
            _LOGGER.warning(f"⚠️  First refresh failed (will retry): {e}")

        # Сохраняем coordinator в hass.data
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        _LOGGER.info(f"✅ Coordinator stored")

        # Устанавливаем platforms
        try:
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            _LOGGER.info(f"✅ Platforms configured: {PLATFORMS}")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to set up platforms: {e}", exc_info=True)
            return False

        # Регистрируем services
        try:
            from services import async_setup_services
            await async_setup_services(hass)
            _LOGGER.info("✅ Services registered")
        except Exception as e:
            _LOGGER.warning(f"⚠️  Failed to set up services: {e}")

        _LOGGER.info("🎉 Zeekr integration setup COMPLETE!")

        return True

    except Exception as err:
        _LOGGER.error(f"❌ Error setting up Zeekr: {err}", exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Zeekr integration"""

    _LOGGER.debug(f"Unloading Zeekr integration for entry {entry.entry_id}")

    try:
        # Выгружаем все platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("✅ Zeekr integration unloaded successfully")

            # Выгружаем services если больше нет интеграций
            if not hass.data[DOMAIN]:
                try:
                    from services import async_unload_services
                    await async_unload_services(hass)
                except Exception as e:
                    _LOGGER.warning(f"⚠️  Failed to unload services: {e}")

        return unload_ok

    except Exception as err:
        _LOGGER.error(f"❌ Error unloading Zeekr integration: {err}")
        return False