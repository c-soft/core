"""Test Satel Integra services."""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant.common import MockConfigEntry
from satel_integra import SatelCommandRejectedError, SatelCommandResult, SatelResultCode
from satel_integra.commands import SatelWriteCommand

from homeassistant.components.satel_integra.const import DOMAIN
from homeassistant.const import CONF_CODE, CommonServiceArgument
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from . import MOCK_CODE, MOCK_ENTRY_ID, setup_integration


@pytest.fixture(autouse=True)
async def no_platforms() -> AsyncGenerator[None]:
    """Set up the integration without entity platforms."""
    with patch("homeassistant.components.satel_integra.PLATFORMS", []):
        yield


@pytest.fixture(autouse=True)
async def warsaw_time_zone(hass: HomeAssistant) -> None:
    """Use a time zone with a UTC offset."""
    await hass.config.async_set_time_zone("Europe/Warsaw")


async def _set_time(hass: HomeAssistant, **data: Any) -> None:
    await hass.services.async_call(
        DOMAIN,
        "set_time",
        {CommonServiceArgument.CONFIG_ENTRY_ID: MOCK_ENTRY_ID, **data},
        blocking=True,
    )


async def test_set_time_defaults_to_now(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the panel clock is set to the current local time by default."""
    await setup_integration(hass, mock_config_entry)
    freezer.move_to("2026-11-22 13:04:05+00:00")

    await _set_time(hass)

    mock_satel.set_panel_time.assert_awaited_once_with(
        MOCK_CODE, datetime(2026, 11, 22, 14, 4, 5), wait_for_result=True
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-11-22 15:00:00", datetime(2026, 11, 22, 15, 0, 0)),
        ("2026-07-01T10:30:00+00:00", datetime(2026, 7, 1, 12, 30, 0)),
    ],
)
async def test_set_time_with_datetime(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry: MockConfigEntry,
    value: str,
    expected: datetime,
) -> None:
    """Test a given time is set as local wall-clock time."""
    await setup_integration(hass, mock_config_entry)

    await _set_time(hass, datetime=value)

    mock_satel.set_panel_time.assert_awaited_once_with(
        MOCK_CODE, expected, wait_for_result=True
    )


async def test_set_time_requires_code(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setting the time without a configured code is refused."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={k: v for k, v in mock_config_entry.options.items() if k != CONF_CODE},
    )
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError) as err:
        await _set_time(hass)

    assert err.value.translation_key == "missing_clock_access_code"
    mock_satel.set_panel_time.assert_not_awaited()


async def test_set_time_no_access(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test a code without the clock right reports a validation error."""
    await setup_integration(hass, mock_config_entry)
    mock_satel.set_panel_time.side_effect = SatelCommandRejectedError(
        SatelWriteCommand.SET_RTC_CLOCK,
        SatelCommandResult(SatelResultCode.NO_ACCESS),
    )

    with pytest.raises(ServiceValidationError) as err:
        await _set_time(hass)

    assert err.value.translation_key == "command_no_access"


async def test_set_time_entry_not_loaded(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setting the time of an unloaded entry is refused."""
    await setup_integration(hass, mock_config_entry)
    await hass.config_entries.async_unload(mock_config_entry.entry_id)

    with pytest.raises(ServiceValidationError) as err:
        await _set_time(hass)

    assert err.value.translation_key == "service_config_entry_not_loaded"
    mock_satel.set_panel_time.assert_not_awaited()
