"""Tests for API generation-specific unifiers."""

from __future__ import annotations

from unittest.mock import AsyncMock, create_autospec

import orjson
import pytest
from tadoasync import models_v3
from tadoasync.api_v3 import ApiV3
from tadoasync.api_x import ApiX
from tadoasync.const import TadoLine
from tadoasync.exceptions import TadoError
from tadoasync.unifier import UnifierV3, UnifierX, get_unifier_from_generation

from tests import load_fixture


async def test_unifier_v3_offset_error_logs_and_continues(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Continue unifier when offset retrieval fails for v3 device."""
    v3_devices = orjson.loads(load_fixture("devices.json"))
    v3_device = models_v3.Device.from_dict(v3_devices[1])

    api_v3 = create_autospec(ApiV3, instance=True)
    api_v3.get_devices = AsyncMock(return_value=[v3_device])
    api_v3.get_device_temperature_offset = AsyncMock(side_effect=TadoError("boom"))

    unifier = UnifierV3(api_v3)

    with caplog.at_level("WARNING"):
        devices_unified = await unifier.get_devices()

    assert len(devices_unified) == 1
    assert devices_unified[0].serial == v3_device.serial_no
    assert devices_unified[0].temperature_offset is None
    assert "Failed to get temperature offset for device SerialNo2: boom" in caplog.text


def test_get_unifier_from_generation_v3() -> None:
    """Build a v3 unifier for PRE_LINE_X generation."""
    api_x = create_autospec(ApiX, instance=True)
    api_v3 = create_autospec(ApiV3, instance=True)
    unifier = get_unifier_from_generation(TadoLine.PRE_LINE_X, api_x, api_v3)
    assert isinstance(unifier, UnifierV3)


def test_get_unifier_from_generation_x() -> None:
    """Build an X unifier for LINE_X generation."""
    api_x = create_autospec(ApiX, instance=True)
    api_v3 = create_autospec(ApiV3, instance=True)
    unifier = get_unifier_from_generation(TadoLine.LINE_X, api_x, api_v3)
    assert isinstance(unifier, UnifierX)


def test_get_unifier_from_generation_unknown_line() -> None:
    """Raise when no generation is available."""
    api_x = create_autospec(ApiX, instance=True)
    api_v3 = create_autospec(ApiV3, instance=True)
    with pytest.raises(
        TadoError,
        match=r"Tado Line not set\. Cannot get unified devices\.",
    ):
        get_unifier_from_generation(None, api_x, api_v3)
