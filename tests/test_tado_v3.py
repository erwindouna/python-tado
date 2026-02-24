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

from .const import TADO_API_URL, TADO_EIQ_URL, TADO_TOKEN_URL


async def test_get_zones(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get zones."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones",
        status=200,
        body=load_fixture(filename="zones.json"),
    )
    assert await python_tado.api_v3.get_zones() == snapshot


async def test_get_devices(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get devices."""
    responses.get(
        f"{TADO_API_URL}/homes/1/devices",
        status=200,
        body=load_fixture(filename="devices.json"),
    )
    assert await python_tado.api_v3.get_devices() == snapshot


async def test_get_device(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get device by serial."""
    responses.get(
        f"{TADO_API_URL}/homes/1/devices/SerialNo1",
        status=200,
        body=load_fixture(filename="device_info.json"),
    )
    assert await python_tado.api_v3.get_device(serial_no="SerialNo1") == snapshot


async def test_get_device_temperature_offset(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get device temperature offset."""
    responses.get(
        f"{TADO_API_URL}/devices/SerialNo1/temperatureOffset",
        status=200,
        body=load_fixture(filename="device_info_attribute.json"),
    )
    assert (
        await python_tado.api_v3.get_device_temperature_offset(serial_no="SerialNo1")
        == snapshot
    )
