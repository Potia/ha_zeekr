# custom_components/zeekr/coordinator.py
"""Data Coordinator для Zeekr интеграции"""

import logging
import sys
import os
from datetime import timedelta
from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Добавляем путь для импорта
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


class ZeekrDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Zeekr data from API"""

    def __init__(self, hass: HomeAssistant, api_client):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

        self.api_client = api_client

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Zeekr API."""
        try:
            _LOGGER.debug("Fetching Zeekr vehicle data")

            # Получаем список автомобилей
            success, vehicles = await self.hass.async_add_executor_job(
                self.api_client.get_vehicles
            )

            if not success:
                raise UpdateFailed("Failed to fetch vehicle list")

            # Для каждого автомобиля получаем статус
            vehicles_data = {}
            for vin in vehicles:
                success, status = await self.hass.async_add_executor_job(
                    self.api_client.get_vehicle_status, vin
                )

                if success and status:
                    vehicles_data[vin] = status
                else:
                    _LOGGER.warning(f"Failed to fetch status for {vin}")

            if not vehicles_data:
                raise UpdateFailed("No vehicle data received")

            _LOGGER.debug(f"Successfully fetched data for {len(vehicles_data)} vehicles")

            return vehicles_data

        except Exception as err:
            _LOGGER.error(f"Error fetching Zeekr data: {err}")
            raise UpdateFailed(f"Error communicating with Zeekr API: {err}")