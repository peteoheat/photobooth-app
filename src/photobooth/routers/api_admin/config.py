import logging
import platform
from typing import Any, AnyStr

from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError

from ... import ACTIVE_EVENT_NAME, sanitize_event_name
from ...appconfig import appconfig
from ...container import container

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["admin", "config"])


def _restart_if_event_changed(configurable: str, background_tasks: BackgroundTasks):
    """The event determines the data paths which are set on app start only. If the saved event differs from the one the app is
    running with, restart the app automatically if possible, otherwise inform the user to restart manually."""
    if configurable != "app":
        return

    saved_event_name = sanitize_event_name(appconfig.common.event_name)
    if saved_event_name == ACTIVE_EVENT_NAME:
        return

    logger.warning(
        f"event changed from '{ACTIVE_EVENT_NAME or '<default>'}' to '{saved_event_name or '<default>'}'. A restart is required for the change to take effect!"
    )

    if platform.system() == "Linux":
        logger.warning("restarting the app now to switch the event. If the app is not running as systemd service, restart it manually!")
        # run after the response is sent, so the UI receives the confirmation of the saved config before the app goes down
        background_tasks.add_task(container.system_service.util_systemd_control, "restart")
    else:
        logger.warning("automatic restart is not supported on this platform, please restart the app manually to switch the event!")


@router.get("/list")
def api_get_configurables():
    return container.config_service.list_configurables()


@router.delete("")
def api_reset_all_config():
    raise NotImplementedError


@router.delete("/{configurable}")
def api_reset_config(configurable: str, background_tasks: BackgroundTasks):
    container.config_service.reset(configurable)

    _restart_if_event_changed(configurable, background_tasks)


@router.get("/{configurable}/schema")
def api_get_config_schema(configurable: str):
    return container.config_service.get_schema(configurable)


@router.get("/{configurable}")
def api_get_config_current_active(configurable: str):
    return container.config_service.get_current(configurable, True)


@router.patch("/{configurable}")
def api_post_config_current(configurable: str, updated_config: dict[AnyStr, Any], background_tasks: BackgroundTasks, reload: bool = False):
    """Update the configuration for appconfig (configurable=app) or a plugin (example configurable="photobooth.plugins.gpio_lights")
    The configuration is persisted also after update.
    updated_config is a generic type valid to receive json objects instead of a pydantic model because depending on the configurable
    the model is different.

    Args:
        configurable (str): app for appconfig, otherwise str with plugin name to update the config for. Defaults to None.
        updated_config (dict[AnyStr, Any]): valid json that is validated against appconfig or plugin config pydantic models
    """

    # persists also automatically
    try:
        container.config_service.validate_and_set_current_and_persist(configurable, updated_config)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    if reload:
        logger.info("reload parameter is set, so all registered services are reloaded now. This may take some time...")
        container.reload()

    _restart_if_event_changed(configurable, background_tasks)
