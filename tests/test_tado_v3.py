"""Tests for the Python Tado X models."""

from aioresponses import aioresponses
from tadoasync import (
    Tado,
)

from syrupy import SnapshotAssertion
from tests import load_fixture

from .const import TADO_API_URL


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
