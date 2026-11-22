"""Services for the Satel Integra integration."""

from datetime import datetime
from enum import StrEnum

import probatio

from homeassistant.const import CONF_CODE, CommonServiceArgument
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, service
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import SatelConfigEntry
from .helpers import async_validate_command


class SatelIntegraService(StrEnum):
    """Store keys for Satel Integra services."""

    SET_TIME = "set_time"


class SatelIntegraServiceArgument(StrEnum):
    """Store keys for Satel Integra service arguments."""

    DATETIME = "datetime"


SET_TIME_SCHEMA = probatio.Schema(
    {
        probatio.Required(CommonServiceArgument.CONFIG_ENTRY_ID): cv.string,
        probatio.Optional(SatelIntegraServiceArgument.DATETIME): cv.datetime,
    }
)


async def async_set_time(call: ServiceCall) -> None:
    """Set the date and time of a Satel Integra alarm panel."""
    config_entry: SatelConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[CommonServiceArgument.CONFIG_ENTRY_ID]
    )
    code = config_entry.options.get(CONF_CODE)
    if not code:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="missing_clock_access_code",
        )

    value: datetime = call.data.get(SatelIntegraServiceArgument.DATETIME, dt_util.now())
    # The panel keeps local wall-clock time; a naive value is already local.
    if value.tzinfo is not None:
        value = dt_util.as_local(value)

    await async_validate_command(
        config_entry.runtime_data.client.controller.set_panel_time(
            code, value.replace(tzinfo=None), wait_for_result=True
        )
    )


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the Satel Integra integration."""
    hass.services.async_register(
        DOMAIN,
        SatelIntegraService.SET_TIME,
        async_set_time,
        schema=SET_TIME_SCHEMA,
    )
