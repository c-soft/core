"""Constants used in the Mikrotik components."""
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "mikrotik"
DEFAULT_NAME: Final = "Mikrotik"
DEFAULT_API_PORT: Final = 8728
DEFAULT_DETECTION_TIME: Final = 300

ATTR_MANUFACTURER: Final = "Mikrotik"
ATTR_SERIAL_NUMBER: Final = "serial-number"
ATTR_FIRMWARE: Final = "current-firmware"
ATTR_MODEL: Final = "model"

CONF_ARP_PING: Final = "arp_ping"
CONF_FORCE_DHCP: Final = "force_dhcp"
CONF_DETECTION_TIME: Final = "detection_time"


NAME: Final = "name"
INFO: Final = "info"
IDENTITY: Final = "identity"
ARP: Final = "arp"

CAPSMAN: Final = "capsman"
DHCP: Final = "dhcp"
WIRELESS: Final = "wireless"
IS_WIRELESS: Final = "is_wireless"
IS_CAPSMAN: Final = "is_capsman"

MIKROTIK_SERVICES: Final = {
    ARP: "/ip/arp/getall",
    CAPSMAN: "/caps-man/registration-table/getall",
    DHCP: "/ip/dhcp-server/lease/getall",
    IDENTITY: "/system/identity/getall",
    INFO: "/system/routerboard/getall",
    WIRELESS: "/interface/wireless/registration-table/getall",
    IS_WIRELESS: "/interface/wireless/print",
    IS_CAPSMAN: "/caps-man/interface/print",
}

PLATFORMS: Final = [Platform.DEVICE_TRACKER]

ATTR_DEVICE_TRACKER: Final = [
    "comment",
    "mac-address",
    "ssid",
    "interface",
    "signal-strength",
    "signal-to-noise",
    "rx-rate",
    "tx-rate",
    "uptime",
]
