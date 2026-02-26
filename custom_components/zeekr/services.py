# custom_components/zeekr/services.py
"""Services for Zeekr integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import ZeekrDataCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_REFRESH_DATA = "refresh_vehicle_data"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Zeekr integration."""

    async def handle_refresh_data(call: ServiceCall) -> None:
        """Handle the refresh vehicle data service call."""

        _LOGGER.info("📡 Manual data refresh requested")

        # Получаем все coordinators
        for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
            if isinstance(coordinator, ZeekrDataCoordinator):
                _LOGGER.info(f"🔄 Refreshing data for entry {entry_id}")
                await coordinator.async_refresh()

    # Регистрируем service
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_DATA,
        handle_refresh_data,
        description="Manually refresh Zeekr vehicle data",
    )

    _LOGGER.info("✅ Zeekr services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""

    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)
    _LOGGER.info("✅ Zeekr services unloaded")