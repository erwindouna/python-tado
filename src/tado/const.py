"""Constants for the asynchronous Python API for Tado."""

from enum import Enum


class HttpMethod(Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
