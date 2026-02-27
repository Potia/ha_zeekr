# custom_components/zeekr/button.py
"""Button platform for Zeekr integration"""

import logging
from typing import Any

from homeassistant.components.button import (
    ButtonEntity,
    ButtonDeviceClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZeekrDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigType,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zeekr buttons"""

    coordinator: ZeekrDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # Всегда создаем общую кнопку
    entities.append(ZeekrRefreshButton(coordinator))

    # Создаем кнопку для каждой машины (если данные загружены)
    async def add_vehicle_buttons():
        """Отложенное добавление кнопок машин"""
        await coordinator.async_request_refresh()

        if coordinator.data:
            vehicle_entities = []
            for vin in coordinator.data.keys():
                if vin:
                    vehicle_entities.append(ZeekrRefreshVehicleButton(coordinator, vin))

            if vehicle_entities:
                async_add_entities(vehicle_entities)
                _LOGGER.info(f"✅ Added {len(vehicle_entities)} vehicle buttons")

    # Добавляем общую кнопку сразу
    async_add_entities(entities)

    # Добавляем кнопки машин после загрузки данных
    hass.async_create_task(add_vehicle_buttons())


class ZeekrRefreshButton(CoordinatorEntity, ButtonEntity):
    """Global refresh button for all vehicles"""

    _attr_name = "Refresh All Vehicles"
    _attr_icon = "mdi:refresh"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_has_entity_name = False

    def __init__(self, coordinator: ZeekrDataCoordinator):
        """Initialize button"""
        super().__init__(coordinator)
        self.coordinator = coordinator

        # Уникальный ID
        self._attr_unique_id = f"{DOMAIN}_refresh_all"

        # Это общее устройство, не привязано к конкретной машине
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "global")},
            "name": "Zeekr",
            "manufacturer": "Zeekr",
            "model": "API",
        }

    async def async_press(self) -> None:
        """
        Вызывается когда пользователь нажимает на кнопку

        ОБЪЯСНЕНИЕ:
        1. Логируем нажатие
        2. Вызываем async_refresh() координатора
        3. Координатор запрашивает новые данные с сервера
        4. Все датчики обновляются автоматически
        """
        _LOGGER.info("🔄 [REFRESH] Принудительное обновление всех автомобилей...")

        try:
            await self.coordinator.async_refresh()
            _LOGGER.info("✅ [REFRESH] Обновление завершено успешно!")
        except Exception as e:
            _LOGGER.error(f"❌ [REFRESH] Ошибка при обновлении: {e}")
            raise


class ZeekrRefreshVehicleButton(CoordinatorEntity, ButtonEntity):
    """Refresh button for individual vehicle"""

    _attr_icon = "mdi:refresh"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_has_entity_name = True
    _attr_name = "Refresh"

    def __init__(self, coordinator: ZeekrDataCoordinator, vin: str):
        """Initialize button"""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.vin = vin

        # Уникальный ID
        self._attr_unique_id = f"{DOMAIN}_{vin}_refresh"

        # Привязываем к устройству конкретной машины
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": f"Zeekr {vin}",
            "manufacturer": "Zeekr",
            "model": "EV",
        }

    async def async_press(self) -> None:
        """
        Вызывается когда пользователь нажимает на кнопку
        """
        _LOGGER.info(f"🔄 [REFRESH] Принудительное обновление для {self.vin}...")

        try:
            await self.coordinator.async_refresh()
            _LOGGER.info(f"✅ [REFRESH] Обновление для {self.vin} завершено!")
        except Exception as e:
            _LOGGER.error(f"❌ [REFRESH] Ошибка при обновлении {self.vin}: {e}")
            raise

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator"""
        self.async_write_ha_state()