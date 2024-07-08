"""Constants for the asynchronous Python API for Tado."""

from enum import Enum

CONST_MODE_OFF = "OFF"
CONST_MODE_SMART_SCHEDULE = "SMART_SCHEDULE"
CONST_MODE_AUTO = "AUTO"
CONST_MODE_COOL = "COOL"
CONST_MODE_HEAT = "HEAT"
CONST_MODE_DRY = "DRY"
CONST_MODE_FAN = "FAN"


class HttpMethod(Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
