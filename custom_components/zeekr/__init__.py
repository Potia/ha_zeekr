# custom_components/zeekr/__init__.py
"""Zeekr integration for Home Assistant"""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .zeekr_api import ZeekrAPI
from .coordinator import ZeekrDataCoordinator
from .storage import token_storage

_LOGGER = logging.getLogger(__name__)

# ✅ ДОБАВЛЯЕМ BUTTON
PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zeekr integration"""

    _LOGGER.info(f"🔧 Setting up Zeekr integration for entry {entry.entry_id}")

    try:
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

        # Создаем API клиент
        api_client = ZeekrAPI(
            access_token=tokens.get('accessToken'),
            user_id=tokens.get('userId'),
            client_id=tokens.get('clientId'),
            device_id=tokens.get('device_id')
        )
        _LOGGER.info("✅ API client created")

        # Создаем coordinator
        coordinator = ZeekrDataCoordinator(hass, api_client)
        _LOGGER.info("✅ Coordinator created")

        # Получаем первые данные
        try:
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.info("✅ First data refresh successful")
        except Exception as e:
            _LOGGER.warning(f"⚠️  First refresh failed: {e}")

        # Сохраняем coordinator
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        # ✅ УСТАНАВЛИВАЕМ PLATFORMS (включая BUTTON)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info(f"✅ Platforms configured: {PLATFORMS}")

        _LOGGER.info("🎉 Zeekr integration setup COMPLETE!")

        return True

    except Exception as err:
        _LOGGER.error(f"❌ Error setting up Zeekr: {err}", exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Zeekr integration"""

    _LOGGER.debug(f"Unloading Zeekr integration")

    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("✅ Zeekr integration unloaded")

        return unload_ok

    except Exception as err:
        _LOGGER.error(f"❌ Error unloading Zeekr: {err}")
        return False