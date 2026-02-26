# custom_components/zeekr/config_flow.py
"""Config flow for Zeekr integration"""

import logging
from typing import Any, Dict, Optional
import sys
import os

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_MOBILE, CONF_SMS_CODE

_LOGGER = logging.getLogger(__name__)


class ZeekrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zeekr"""

    VERSION = 1

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

            if not mobile or len(mobile) < 10:
                errors["base"] = "invalid_phone"
            else:
                try:
                    _LOGGER.debug(f"Requesting SMS code for {mobile}")

                    # Добавляем текущую папку в sys.path
                    current_dir = os.path.dirname(__file__)
                    if current_dir not in sys.path:
                        sys.path.insert(0, current_dir)

                    # Импортируем auth
                    from auth import ZeekrAuth

                    auth = ZeekrAuth()

                    # Запрашиваем SMS код
                    def request_sms():
                        success, msg = auth.request_sms_code(mobile)
                        return success, msg

                    success, msg = await self.hass.async_add_executor_job(request_sms)

                    if success:
                        # Сохраняем мобильный для следующего шага
                        self.mobile = mobile
                        self.auth = auth
                        return await self.async_step_sms_code()
                    else:
                        _LOGGER.error(f"Failed to send SMS: {msg}")
                        errors["base"] = "cannot_send_sms"

                except ImportError as e:
                    _LOGGER.error(f"Import error: {e}", exc_info=True)
                    errors["base"] = "import_error"
                except Exception as e:
                    _LOGGER.error(f"Error requesting SMS: {e}", exc_info=True)
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MOBILE): str,
            }),
            errors=errors,
        )

    async def async_step_sms_code(
            self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle SMS code input step"""

        errors: Dict[str, str] = {}

        if user_input is not None:
            sms_code = user_input.get(CONF_SMS_CODE, "").strip()

            if not sms_code or len(sms_code) < 4:
                errors["base"] = "invalid_code"
            else:
                try:
                    _LOGGER.debug("Starting 3-step authentication")

                    # Добавляем текущую папку в sys.path
                    current_dir = os.path.dirname(__file__)
                    if current_dir not in sys.path:
                        sys.path.insert(0, current_dir)

                    from storage import token_storage

                    auth = self.auth
                    mobile = self.mobile

                    # ШАГ 1: SMS логин
                    def sms_login():
                        success, tokens = auth.login_with_sms(mobile, sms_code)
                        return success, tokens

                    success, toc_tokens = await self.hass.async_add_executor_job(sms_login)

                    if not success:
                        _LOGGER.error("SMS login failed")
                        errors["base"] = "invalid_auth"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE): str,
                            }),
                            errors=errors,
                        )

                    jwt_token = toc_tokens.get('jwtToken')
                    auth.mobile = mobile

                    # ШАГ 2: Получение Auth Code
                    def get_auth_code():
                        success, code = auth.get_auth_code(jwt_token)
                        return success, code

                    success, auth_code = await self.hass.async_add_executor_job(get_auth_code)

                    if not success or not auth_code:
                        _LOGGER.error("Failed to get auth code")
                        errors["base"] = "cannot_get_auth_code"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE): str,
                            }),
                            errors=errors,
                        )

                    # ШАГ 3: Логин с Auth Code
                    def auth_code_login():
                        success, tokens = auth.login_with_auth_code(auth_code)
                        return success, tokens

                    success, secure_tokens = await self.hass.async_add_executor_job(auth_code_login)

                    if not success or not secure_tokens:
                        _LOGGER.error("Failed to get secure tokens")
                        errors["base"] = "cannot_get_secure_tokens"
                        return self.async_show_form(
                            step_id="sms_code",
                            data_schema=vol.Schema({
                                vol.Required(CONF_SMS_CODE): str,
                            }),
                            errors=errors,
                        )

                    # Сохраняем токены
                    _LOGGER.info(f"Saving tokens: {list(secure_tokens.keys())}")

                    def save_tokens():
                        print(f"[ConfigFlow] Attempting to save tokens to {token_storage.filename}")
                        token_storage.save_tokens(secure_tokens)
                        # Проверяем что сохранилось
                        import os
                        if os.path.exists(token_storage.filename):
                            print(f"[ConfigFlow] ✅ Файл создан: {token_storage.filename}")
                        else:
                            print(f"[ConfigFlow] ❌ Файл не создан!")

                    await self.hass.async_add_executor_job(save_tokens)

                    _LOGGER.info("Tokens saved successfully")

                    _LOGGER.info("Authentication successful!")

                    return self.async_abort(reason="auth_successful")

                except Exception as e:
                    _LOGGER.error(f"Error during authentication: {e}", exc_info=True)
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="sms_code",
            data_schema=vol.Schema({
                vol.Required(CONF_SMS_CODE): str,
            }),
            errors=errors,
        )