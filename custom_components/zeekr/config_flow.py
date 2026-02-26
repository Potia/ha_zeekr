# custom_components/zeekr/config_flow.py
"""Config flow for Zeekr integration"""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_MOBILE, CONF_SMS_CODE

_LOGGER = logging.getLogger(__name__)


class ZeekrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zeekr"""

    VERSION = 1

    def __init__(self):
        """Initialize config flow"""
        self.mobile: Optional[str] = None
        self.auth_instance = None

    async def async_step_user(
            self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step"""

        errors: Dict[str, str] = {}

        # Проверяем, не уже ли настроено
        await self.async_set_unique_id("zeekr_main")
        self._abort_if_unique_id_configured()

        if user_input is not None:
            mobile = user_input.get(CONF_MOBILE, "").strip()

            if not mobile:
                errors["base"] = "invalid_phone"
            else:
                try:
                    # Импортируем только здесь, чтобы избежать проблем
                    import sys
                    import os

                    # Добавляем родительскую папку в sys.path
                    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)

                    # Импортируем auth
                    from auth import ZeekrAuth

                    # Создаем auth объект
                    auth = ZeekrAuth()
                    self.auth_instance = auth
                    self.mobile = mobile

                    # Запрашиваем SMS код
                    success, msg = await self.hass.async_add_executor_job(
                        auth.request_sms_code, mobile
                    )

                    if success:
                        # Переходим к следующему шагу
                        return await self.async_step_sms_code()
                    else:
                        _LOGGER.error(f"Failed to send SMS: {msg}")
                        errors["base"] = "cannot_send_sms"

                except ImportError as err:
                    _LOGGER.error(f"Import error: {err}")
                    errors["base"] = "import_error"
                except Exception as err:
                    _LOGGER.error(f"Error requesting SMS: {err}")
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MOBILE, default=""): str,
            }),
            errors=errors,
            description_placeholders={
                "hint": "例如: 13812345678"
            }
        )

    async def async_step_sms_code(
            self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle SMS code input step"""

        errors: Dict[str, str] = {}

        if user_input is not None:
            sms_code = user_input.get(CONF_SMS_CODE, "").strip()

            if not sms_code:
                errors["base"] = "invalid_code"
            else:
                try:
                    import sys
                    import os

                    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)

                    from storage import token_storage

                    auth = self.auth_instance

                    _LOGGER.debug("Starting 3-step authentication")

                    # ШАГ 1: SMS логин
                    _LOGGER.debug("Step 1: SMS login")
                    success, toc_tokens = await self.hass.async_add_executor_job(
                        auth.login_with_sms, self.mobile, sms_code
                    )

                    if not success:
                        _LOGGER.error("SMS login failed")
                        errors["base"] = "invalid_auth"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE, default=""): str,
                            }),
                            errors=errors,
                        )

                    jwt_token = toc_tokens.get('jwtToken')
                    if not jwt_token:
                        _LOGGER.error("No JWT token in response")
                        errors["base"] = "no_jwt_token"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE, default=""): str,
                            }),
                            errors=errors,
                        )

                    auth.mobile = self.mobile

                    # ШАГ 2: Получение Auth Code
                    _LOGGER.debug("Step 2: Get auth code")
                    success, auth_code = await self.hass.async_add_executor_job(
                        auth.get_auth_code, jwt_token
                    )

                    if not success or not auth_code:
                        _LOGGER.error("Failed to get auth code")
                        errors["base"] = "cannot_get_auth_code"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE, default=""): str,
                            }),
                            errors=errors,
                        )

                    # ШАГ 3: Логин с Auth Code
                    _LOGGER.debug("Step 3: Auth code login")
                    success, secure_tokens = await self.hass.async_add_executor_job(
                        auth.login_with_auth_code, auth_code
                    )

                    if not success or not secure_tokens:
                        _LOGGER.error("Failed to get secure tokens")
                        errors["base"] = "cannot_get_secure_tokens"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE, default=""): str,
                            }),
                            errors=errors,
                        )

                    # Сохраняем токены
                    _LOGGER.debug("Saving tokens")
                    await self.hass.async_add_executor_job(
                        token_storage.save_tokens, secure_tokens
                    )

                    _LOGGER.info("Authentication successful!")

                    # Успешно завершили конфигурацию
                    return self.async_abort(reason="auth_successful")

                except Exception as err:
                    _LOGGER.error(f"Error during authentication: {err}", exc_info=True)
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="sms_code",
            data_schema=vol.Schema({
                vol.Required(CONF_SMS_CODE, default=""): str,
            }),
            errors=errors,
            description_placeholders={
                "hint": f"SMS code sent to {self.mobile}"
            }
        )