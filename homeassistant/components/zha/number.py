"""Support for ZHA AnalogOutput cluster."""
from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING

import zigpy.exceptions
from zigpy.zcl.foundation import Status

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import discovery
from .core.const import (
    CHANNEL_ANALOG_OUTPUT,
    CHANNEL_LEVEL,
    DATA_ZHA,
    SIGNAL_ADD_ENTITIES,
    SIGNAL_ATTR_UPDATED,
)
from .core.registries import ZHA_ENTITIES
from .entity import ZhaEntity

if TYPE_CHECKING:
    from .core.channels.base import ZigbeeChannel
    from .core.device import ZHADevice

_LOGGER = logging.getLogger(__name__)

STRICT_MATCH = functools.partial(ZHA_ENTITIES.strict_match, Platform.NUMBER)
CONFIG_DIAGNOSTIC_MATCH = functools.partial(
    ZHA_ENTITIES.config_diagnostic_match, Platform.NUMBER
)


UNITS = {
    0: "Square-meters",
    1: "Square-feet",
    2: "Milliamperes",
    3: "Amperes",
    4: "Ohms",
    5: "Volts",
    6: "Kilo-volts",
    7: "Mega-volts",
    8: "Volt-amperes",
    9: "Kilo-volt-amperes",
    10: "Mega-volt-amperes",
    11: "Volt-amperes-reactive",
    12: "Kilo-volt-amperes-reactive",
    13: "Mega-volt-amperes-reactive",
    14: "Degrees-phase",
    15: "Power-factor",
    16: "Joules",
    17: "Kilojoules",
    18: "Watt-hours",
    19: "Kilowatt-hours",
    20: "BTUs",
    21: "Therms",
    22: "Ton-hours",
    23: "Joules-per-kilogram-dry-air",
    24: "BTUs-per-pound-dry-air",
    25: "Cycles-per-hour",
    26: "Cycles-per-minute",
    27: "Hertz",
    28: "Grams-of-water-per-kilogram-dry-air",
    29: "Percent-relative-humidity",
    30: "Millimeters",
    31: "Meters",
    32: "Inches",
    33: "Feet",
    34: "Watts-per-square-foot",
    35: "Watts-per-square-meter",
    36: "Lumens",
    37: "Luxes",
    38: "Foot-candles",
    39: "Kilograms",
    40: "Pounds-mass",
    41: "Tons",
    42: "Kilograms-per-second",
    43: "Kilograms-per-minute",
    44: "Kilograms-per-hour",
    45: "Pounds-mass-per-minute",
    46: "Pounds-mass-per-hour",
    47: "Watts",
    48: "Kilowatts",
    49: "Megawatts",
    50: "BTUs-per-hour",
    51: "Horsepower",
    52: "Tons-refrigeration",
    53: "Pascals",
    54: "Kilopascals",
    55: "Bars",
    56: "Pounds-force-per-square-inch",
    57: "Centimeters-of-water",
    58: "Inches-of-water",
    59: "Millimeters-of-mercury",
    60: "Centimeters-of-mercury",
    61: "Inches-of-mercury",
    62: "°C",
    63: "°K",
    64: "°F",
    65: "Degree-days-Celsius",
    66: "Degree-days-Fahrenheit",
    67: "Years",
    68: "Months",
    69: "Weeks",
    70: "Days",
    71: "Hours",
    72: "Minutes",
    73: "Seconds",
    74: "Meters-per-second",
    75: "Kilometers-per-hour",
    76: "Feet-per-second",
    77: "Feet-per-minute",
    78: "Miles-per-hour",
    79: "Cubic-feet",
    80: "Cubic-meters",
    81: "Imperial-gallons",
    82: "Liters",
    83: "Us-gallons",
    84: "Cubic-feet-per-minute",
    85: "Cubic-meters-per-second",
    86: "Imperial-gallons-per-minute",
    87: "Liters-per-second",
    88: "Liters-per-minute",
    89: "Us-gallons-per-minute",
    90: "Degrees-angular",
    91: "Degrees-Celsius-per-hour",
    92: "Degrees-Celsius-per-minute",
    93: "Degrees-Fahrenheit-per-hour",
    94: "Degrees-Fahrenheit-per-minute",
    95: None,
    96: "Parts-per-million",
    97: "Parts-per-billion",
    98: "%",
    99: "Percent-per-second",
    100: "Per-minute",
    101: "Per-second",
    102: "Psi-per-Degree-Fahrenheit",
    103: "Radians",
    104: "Revolutions-per-minute",
    105: "Currency1",
    106: "Currency2",
    107: "Currency3",
    108: "Currency4",
    109: "Currency5",
    110: "Currency6",
    111: "Currency7",
    112: "Currency8",
    113: "Currency9",
    114: "Currency10",
    115: "Square-inches",
    116: "Square-centimeters",
    117: "BTUs-per-pound",
    118: "Centimeters",
    119: "Pounds-mass-per-second",
    120: "Delta-Degrees-Fahrenheit",
    121: "Delta-Degrees-Kelvin",
    122: "Kilohms",
    123: "Megohms",
    124: "Millivolts",
    125: "Kilojoules-per-kilogram",
    126: "Megajoules",
    127: "Joules-per-degree-Kelvin",
    128: "Joules-per-kilogram-degree-Kelvin",
    129: "Kilohertz",
    130: "Megahertz",
    131: "Per-hour",
    132: "Milliwatts",
    133: "Hectopascals",
    134: "Millibars",
    135: "Cubic-meters-per-hour",
    136: "Liters-per-hour",
    137: "Kilowatt-hours-per-square-meter",
    138: "Kilowatt-hours-per-square-foot",
    139: "Megajoules-per-square-meter",
    140: "Megajoules-per-square-foot",
    141: "Watts-per-square-meter-Degree-Kelvin",
    142: "Cubic-feet-per-second",
    143: "Percent-obscuration-per-foot",
    144: "Percent-obscuration-per-meter",
    145: "Milliohms",
    146: "Megawatt-hours",
    147: "Kilo-BTUs",
    148: "Mega-BTUs",
    149: "Kilojoules-per-kilogram-dry-air",
    150: "Megajoules-per-kilogram-dry-air",
    151: "Kilojoules-per-degree-Kelvin",
    152: "Megajoules-per-degree-Kelvin",
    153: "Newton",
    154: "Grams-per-second",
    155: "Grams-per-minute",
    156: "Tons-per-hour",
    157: "Kilo-BTUs-per-hour",
    158: "Hundredths-seconds",
    159: "Milliseconds",
    160: "Newton-meters",
    161: "Millimeters-per-second",
    162: "Millimeters-per-minute",
    163: "Meters-per-minute",
    164: "Meters-per-hour",
    165: "Cubic-meters-per-minute",
    166: "Meters-per-second-per-second",
    167: "Amperes-per-meter",
    168: "Amperes-per-square-meter",
    169: "Ampere-square-meters",
    170: "Farads",
    171: "Henrys",
    172: "Ohm-meters",
    173: "Siemens",
    174: "Siemens-per-meter",
    175: "Teslas",
    176: "Volts-per-degree-Kelvin",
    177: "Volts-per-meter",
    178: "Webers",
    179: "Candelas",
    180: "Candelas-per-square-meter",
    181: "Kelvins-per-hour",
    182: "Kelvins-per-minute",
    183: "Joule-seconds",
    185: "Square-meters-per-Newton",
    186: "Kilogram-per-cubic-meter",
    187: "Newton-seconds",
    188: "Newtons-per-meter",
    189: "Watts-per-meter-per-degree-Kelvin",
}

ICONS = {
    0: "mdi:temperature-celsius",
    1: "mdi:water-percent",
    2: "mdi:gauge",
    3: "mdi:speedometer",
    4: "mdi:percent",
    5: "mdi:air-filter",
    6: "mdi:fan",
    7: "mdi:flash",
    8: "mdi:current-ac",
    9: "mdi:flash",
    10: "mdi:flash",
    11: "mdi:flash",
    12: "mdi:counter",
    13: "mdi:thermometer-lines",
    14: "mdi:timer",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zigbee Home Automation Analog Output from config entry."""
    entities_to_create = hass.data[DATA_ZHA][Platform.NUMBER]

    unsub = async_dispatcher_connect(
        hass,
        SIGNAL_ADD_ENTITIES,
        functools.partial(
            discovery.async_add_entities,
            async_add_entities,
            entities_to_create,
        ),
    )
    config_entry.async_on_unload(unsub)


@STRICT_MATCH(channel_names=CHANNEL_ANALOG_OUTPUT)
class ZhaNumber(ZhaEntity, NumberEntity):
    """Representation of a ZHA Number entity."""

    def __init__(self, unique_id, zha_device, channels, **kwargs):
        """Init this entity."""
        super().__init__(unique_id, zha_device, channels, **kwargs)
        self._analog_output_channel = self.cluster_channels.get(CHANNEL_ANALOG_OUTPUT)

    async def async_added_to_hass(self):
        """Run when about to be added to hass."""
        await super().async_added_to_hass()
        self.async_accept_signal(
            self._analog_output_channel, SIGNAL_ATTR_UPDATED, self.async_set_state
        )

    @property
    def native_value(self):
        """Return the current value."""
        return self._analog_output_channel.present_value

    @property
    def native_min_value(self):
        """Return the minimum value."""
        min_present_value = self._analog_output_channel.min_present_value
        if min_present_value is not None:
            return min_present_value
        return 0

    @property
    def native_max_value(self):
        """Return the maximum value."""
        max_present_value = self._analog_output_channel.max_present_value
        if max_present_value is not None:
            return max_present_value
        return 1023

    @property
    def native_step(self):
        """Return the value step."""
        resolution = self._analog_output_channel.resolution
        if resolution is not None:
            return resolution
        return super().native_step

    @property
    def name(self):
        """Return the name of the number entity."""
        description = self._analog_output_channel.description
        if description is not None and len(description) > 0:
            return f"{super().name} {description}"
        return super().name

    @property
    def icon(self):
        """Return the icon to be used for this entity."""
        application_type = self._analog_output_channel.application_type
        if application_type is not None:
            return ICONS.get(application_type >> 16, super().icon)
        return super().icon

    @property
    def native_unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        engineering_units = self._analog_output_channel.engineering_units
        return UNITS.get(engineering_units)

    @callback
    def async_set_state(self, attr_id, attr_name, value):
        """Handle value update from channel."""
        self.async_write_ha_state()

    async def async_set_native_value(self, value):
        """Update the current value from HA."""
        num_value = float(value)
        if await self._analog_output_channel.async_set_present_value(num_value):
            self.async_write_ha_state()

    async def async_update(self):
        """Attempt to retrieve the state of the entity."""
        await super().async_update()
        _LOGGER.debug("polling current state")
        if self._analog_output_channel:
            value = await self._analog_output_channel.get_attribute_value(
                "present_value", from_cache=False
            )
            _LOGGER.debug("read value=%s", value)


class ZHANumberConfigurationEntity(ZhaEntity, NumberEntity):
    """Representation of a ZHA number configuration entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_step: float = 1.0
    _zcl_attribute: str

    @classmethod
    def create_entity(
        cls,
        unique_id: str,
        zha_device: ZHADevice,
        channels: list[ZigbeeChannel],
        **kwargs,
    ) -> ZhaEntity | None:
        """Entity Factory.

        Return entity if it is a supported configuration, otherwise return None
        """
        channel = channels[0]
        if (
            cls._zcl_attribute in channel.cluster.unsupported_attributes
            or channel.cluster.get(cls._zcl_attribute) is None
        ):
            _LOGGER.debug(
                "%s is not supported - skipping %s entity creation",
                cls._zcl_attribute,
                cls.__name__,
            )
            return None

        return cls(unique_id, zha_device, channels, **kwargs)

    def __init__(
        self,
        unique_id: str,
        zha_device: ZHADevice,
        channels: list[ZigbeeChannel],
        **kwargs,
    ) -> None:
        """Init this number configuration entity."""
        self._channel: ZigbeeChannel = channels[0]
        super().__init__(unique_id, zha_device, channels, **kwargs)

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._channel.cluster.get(self._zcl_attribute)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value from HA."""
        try:
            res = await self._channel.cluster.write_attributes(
                {self._zcl_attribute: int(value)}
            )
        except zigpy.exceptions.ZigbeeException as ex:
            self.error("Could not set value: %s", ex)
            return
        if not isinstance(res, Exception) and all(
            record.status == Status.SUCCESS for record in res[0]
        ):
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Attempt to retrieve the state of the entity."""
        await super().async_update()
        _LOGGER.debug("polling current state")
        if self._channel:
            value = await self._channel.get_attribute_value(
                self._zcl_attribute, from_cache=False
            )
            _LOGGER.debug("read value=%s", value)


@CONFIG_DIAGNOSTIC_MATCH(channel_names="opple_cluster", models={"lumi.motion.ac02"})
class AqaraMotionDetectionInterval(
    ZHANumberConfigurationEntity, id_suffix="detection_interval"
):
    """Representation of a ZHA on off transition time configuration entity."""

    _attr_native_min_value: float = 2
    _attr_native_max_value: float = 65535
    _zcl_attribute: str = "detection_interval"


@CONFIG_DIAGNOSTIC_MATCH(channel_names=CHANNEL_LEVEL)
class OnOffTransitionTimeConfigurationEntity(
    ZHANumberConfigurationEntity, id_suffix="on_off_transition_time"
):
    """Representation of a ZHA on off transition time configuration entity."""

    _attr_native_min_value: float = 0x0000
    _attr_native_max_value: float = 0xFFFF
    _zcl_attribute: str = "on_off_transition_time"


@CONFIG_DIAGNOSTIC_MATCH(channel_names=CHANNEL_LEVEL)
class OnLevelConfigurationEntity(ZHANumberConfigurationEntity, id_suffix="on_level"):
    """Representation of a ZHA on level configuration entity."""

    _attr_native_min_value: float = 0x00
    _attr_native_max_value: float = 0xFF
    _zcl_attribute: str = "on_level"


@CONFIG_DIAGNOSTIC_MATCH(channel_names=CHANNEL_LEVEL)
class OnTransitionTimeConfigurationEntity(
    ZHANumberConfigurationEntity, id_suffix="on_transition_time"
):
    """Representation of a ZHA on transition time configuration entity."""

    _attr_native_min_value: float = 0x0000
    _attr_native_max_value: float = 0xFFFE
    _zcl_attribute: str = "on_transition_time"


@CONFIG_DIAGNOSTIC_MATCH(channel_names=CHANNEL_LEVEL)
class OffTransitionTimeConfigurationEntity(
    ZHANumberConfigurationEntity, id_suffix="off_transition_time"
):
    """Representation of a ZHA off transition time configuration entity."""

    _attr_native_min_value: float = 0x0000
    _attr_native_max_value: float = 0xFFFE
    _zcl_attribute: str = "off_transition_time"


@CONFIG_DIAGNOSTIC_MATCH(channel_names=CHANNEL_LEVEL)
class DefaultMoveRateConfigurationEntity(
    ZHANumberConfigurationEntity, id_suffix="default_move_rate"
):
    """Representation of a ZHA default move rate configuration entity."""

    _attr_native_min_value: float = 0x00
    _attr_native_max_value: float = 0xFE
    _zcl_attribute: str = "default_move_rate"


@CONFIG_DIAGNOSTIC_MATCH(channel_names=CHANNEL_LEVEL)
class StartUpCurrentLevelConfigurationEntity(
    ZHANumberConfigurationEntity, id_suffix="start_up_current_level"
):
    """Representation of a ZHA startup current level configuration entity."""

    _attr_native_min_value: float = 0x00
    _attr_native_max_value: float = 0xFF
    _zcl_attribute: str = "start_up_current_level"


@CONFIG_DIAGNOSTIC_MATCH(
    channel_names="tuya_manufacturer",
    manufacturers={
        "_TZE200_htnnfasr",
    },
)
class TimerDurationMinutes(ZHANumberConfigurationEntity, id_suffix="timer_duration"):
    """Representation of a ZHA timer duration configuration entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon: str = ICONS[14]
    _attr_native_min_value: float = 0x00
    _attr_native_max_value: float = 0x257
    _attr_unit_of_measurement: str | None = UNITS[72]
    _zcl_attribute: str = "timer_duration"


@CONFIG_DIAGNOSTIC_MATCH(
    channel_names="ikea_airpurifier", models={"STARKVIND Air purifier"}
)
class FilterLifeTime(ZHANumberConfigurationEntity, id_suffix="filter_life_time"):
    """Representation of a ZHA timer duration configuration entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon: str = ICONS[14]
    _attr_native_min_value: float = 0x00
    _attr_native_max_value: float = 0xFFFFFFFF
    _attr_unit_of_measurement: str | None = UNITS[72]
    _zcl_attribute: str = "filter_life_time"
