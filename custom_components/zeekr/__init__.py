# custom_components/zeekr/__init__.py
"""Zeekr integration for Home Assistant"""

import logging
import os
import json
from typing import Final
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .zeekr_api import ZeekrAPI
from .coordinator import ZeekrDataCoordinator
from .zeekr_storage import token_storage

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
        # ✅ ЗАГРУЖАЕМ ТОКЕНЫ ИЗ ENTRY (в приоритете)
        tokens = dict(entry.data)

        # Резервно проверяем файл (для старых установок)
        if not tokens or not tokens.get('accessToken'):
            _LOGGER.warning("⚠️ No tokens in entry.data, trying file storage...")
            tokens = token_storage.load_tokens()

            if tokens:
                # Обновляем entry с токенами из файла
                hass.config_entries.async_update_entry(entry, data=tokens)
                _LOGGER.info("✅ Tokens migrated from file to entry")

        if not tokens or not tokens.get('accessToken'):
            _LOGGER.error("❌ No tokens found in entry or file storage")
            return False

        _LOGGER.info(f"✅ Tokens loaded from entry.data")

        # Проверяем необходимые поля
        required_fields = ['accessToken', 'userId', 'clientId', 'device_id']
        missing_fields = [f for f in required_fields if f not in tokens or not tokens[f]]

        if missing_fields:
            _LOGGER.error(f"❌ Missing required token fields: {missing_fields}")
            return False

        # Создаем папку для сохранения ответов сервера
        try:
            responses_dir = os.path.join(hass.config.path('www'), 'zeekr_responses')
            os.makedirs(responses_dir, exist_ok=True)
            _LOGGER.info(f"📁 Responses directory: {responses_dir}")
        except Exception as e:
            _LOGGER.error(f"❌ Failed to create responses directory: {e}")
            responses_dir = None

        # Создаем API клиент
        api_client = ZeekrAPI(
            access_token=tokens.get('accessToken'),
            user_id=tokens.get('userId'),
            client_id=tokens.get('clientId'),
            device_id=tokens.get('device_id')
        )
        _LOGGER.info("✅ API client created")

        # Создаем coordinator
        coordinator = ZeekrDataCoordinator(hass, api_client, responses_dir)
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

        # ========== РЕГИСТРИРУЕМ SERVICES ==========

        async def handle_save_response(call: ServiceCall) -> None:
            """
            Сервис для ручного сохранения ответа сервера

            Использование:
            service: zeekr.save_response
            data:
              filename: "manual_response.json"
              description: "Ответ при ошибке"
            """
            _LOGGER.info("📥 Manual save response called")

            try:
                if not responses_dir:
                    _LOGGER.error("❌ Responses directory not configured")
                    return

                filename = call.data.get('filename', f'response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                description = call.data.get('description', 'Manual save')

                # Получаем последние данные
                for entry_id, coord in hass.data.get(DOMAIN, {}).items():
                    if isinstance(coord, ZeekrDataCoordinator):
                        if coord.last_response:
                            filepath = os.path.join(responses_dir, filename)

                            response_with_metadata = {
                                "_metadata": {
                                    "saved_at": datetime.now().isoformat(),
                                    "description": description,
                                    "entry_id": entry_id
                                },
                                "data": coord.last_response
                            }

                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(response_with_metadata, f, ensure_ascii=False, indent=2)

                            _LOGGER.info(f"✅ Response saved to {filepath}")
                            return

                _LOGGER.warning("⚠️ No vehicle data available to save")

            except Exception as e:
                _LOGGER.error(f"❌ Error saving response: {e}", exc_info=True)

        async def handle_refresh_and_save(call: ServiceCall) -> None:
            """
            Обновляет данные и сохраняет ответ

            Использование:
            service: zeekr.refresh_and_save
            data:
              description: "Информация при зарядке"
            """
            _LOGGER.info("🔄 Refresh and save called")

            try:
                if not responses_dir:
                    _LOGGER.error("❌ Responses directory not configured")
                    return

                for entry_id, coord in hass.data.get(DOMAIN, {}).items():
                    if isinstance(coord, ZeekrDataCoordinator):
                        await coord.async_refresh()

                        # Сохраняем ответ с описанием
                        if coord.last_response:
                            description = call.data.get('description', 'Auto refresh')
                            filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            filepath = os.path.join(responses_dir, filename)

                            response_with_metadata = {
                                "_metadata": {
                                    "saved_at": datetime.now().isoformat(),
                                    "description": description,
                                    "entry_id": entry_id,
                                    "auto_save": True
                                },
                                "data": coord.last_response
                            }

                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(response_with_metadata, f, ensure_ascii=False, indent=2)

                            _LOGGER.info(f"✅ Response auto-saved to {filepath}")

            except Exception as e:
                _LOGGER.error(f"❌ Error in refresh and save: {e}", exc_info=True)

        async def handle_list_responses(call: ServiceCall) -> None:
            """
            Выводит список всех сохраненных ответов

            Использование:
            service: zeekr.list_responses
            """
            _LOGGER.info("📋 Listing saved responses")

            try:
                if not responses_dir:
                    _LOGGER.error("❌ Responses directory not configured")
                    return

                if os.path.exists(responses_dir):
                    files = os.listdir(responses_dir)
                    json_files = [f for f in files if f.endswith('.json')]

                    if json_files:
                        _LOGGER.info(f"📁 Found {len(json_files)} response files:")
                        for f in json_files:
                            filepath = os.path.join(responses_dir, f)
                            size = os.path.getsize(filepath)
                            _LOGGER.info(f"  - {f} ({size} bytes)")
                    else:
                        _LOGGER.info("No response files found")
                else:
                    _LOGGER.warning(f"Responses directory not found: {responses_dir}")

            except Exception as e:
                _LOGGER.error(f"❌ Error listing responses: {e}", exc_info=True)

        # ✅ РЕГИСТРИРУЕМ БЕЗ 'description' (старые версии HA не поддерживают)
        hass.services.async_register(
            DOMAIN,
            'save_response',
            handle_save_response
        )

        hass.services.async_register(
            DOMAIN,
            'refresh_and_save',
            handle_refresh_and_save
        )

        hass.services.async_register(
            DOMAIN,
            'list_responses',
            handle_list_responses
        )

        _LOGGER.info("✅ Zeekr services registered:")
        _LOGGER.info("   - zeekr.save_response")
        _LOGGER.info("   - zeekr.refresh_and_save")
        _LOGGER.info("   - zeekr.list_responses")

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

        # Удаляем зарегистрированные сервисы
        hass.services.async_remove(DOMAIN, 'save_response')
        hass.services.async_remove(DOMAIN, 'refresh_and_save')
        hass.services.async_remove(DOMAIN, 'list_responses')
        _LOGGER.info("✅ Zeekr services removed")

        return unload_ok

    except Exception as err:
        _LOGGER.error(f"❌ Error unloading Zeekr: {err}")
        return False