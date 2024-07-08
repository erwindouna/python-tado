"""Constants for the asynchronous Python API for Tado."""

from enum import Enum

CONST_HVAC_COOL = "COOLING"
CONST_HVAC_DRY = "DRYING"
CONST_HVAC_FAN = "FAN"
CONST_HVAC_HEAT = "HEATING"
CONST_HVAC_HOT_WATER = "HOT_WATER"
CONST_HVAC_IDLE = "IDLE"
CONST_HVAC_OFF = "OFF"


class HttpMethod(Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
