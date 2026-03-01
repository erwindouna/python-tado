"""Tests for the Python Tado X models."""

from aioresponses import aioresponses
from tadoasync import (
    Tado,
)

from syrupy import SnapshotAssertion
from tests import load_fixture

from .const import TADO_X_API_URL


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
