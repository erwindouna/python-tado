"""Tests for the Python Tado X models."""

import asyncio
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientResponse, ClientResponseError, RequestInfo
from aioresponses import CallbackResult, aioresponses
from tadoasync import (
    Tado,
)
from tadoasync.exceptions import (
    TadoAuthenticationError,
    TadoBadRequestError,
    TadoConnectionError,
    TadoError,
    TadoReadingError,
)
from tadoasync.tadoasync import DEVICE_AUTH_URL, DeviceActivationStatus

from syrupy import SnapshotAssertion
from tests import load_fixture

from .const import TADO_X_API_URL, TADO_EIQ_URL, TADO_TOKEN_URL


async def test_get_rooms_and_devices(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get home."""
    responses.get(
        f"{TADO_X_API_URL}/homes/1/roomsAndDevices",
        status=200,
        body=load_fixture(folder="LINE_X", filename="roomsAndDevices.json"),
    )
    assert await python_tado.api_x.get_rooms_and_devices() == snapshot
