"""Unifier classes for API generation-specific response handling."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from tadoasync import models_unified as unified_models
from tadoasync.const import INSIDE_TEMPERATURE_MEASUREMENT, TadoLine
from tadoasync.exceptions import TadoError

if TYPE_CHECKING:
    from tadoasync.api_v3 import ApiV3
    from tadoasync.api_x import ApiX

_LOGGER = logging.getLogger(__name__)


class DeviceUnifier(Protocol):  # pylint: disable=too-few-public-methods
    """Interface class for API generation device unifiers."""

    async def get_devices(self) -> list[unified_models.Device]:
        """Return unified devices for this API generation."""


class UnifierV3:  # pylint: disable=too-few-public-methods
    """Unifier for the v3 Tado API."""

    def __init__(self, api_v3: ApiV3) -> None:
        """Initialize the v3 unifier."""
        self._api_v3 = api_v3

    async def get_devices(self) -> list[unified_models.Device]:
        """Get devices in unified format from the Tado v3 API."""
        devices = await self._api_v3.get_devices()
        if not devices:
            raise TadoError("No devices found for the home")

        devices_unified: list[unified_models.Device] = []
        for v3_device in devices:
            offset = None
            if INSIDE_TEMPERATURE_MEASUREMENT in v3_device.characteristics.capabilities:
                try:
                    offset = await self._api_v3.get_device_temperature_offset(
                        v3_device.serial_no,
                    )
                except TadoError as err:
                    _LOGGER.warning(
                        "Failed to get temperature offset for device %s: %s",
                        v3_device.serial_no,
                        err,
                    )
            devices_unified.append(unified_models.Device.from_v3(v3_device, offset))
        return devices_unified


class UnifierX:  # pylint: disable=too-few-public-methods
    """Unifier for the Tado X API."""

    def __init__(self, api_x: ApiX) -> None:
        """Initialize the Tado X unifier."""
        self._api_x = api_x

    async def get_devices(self) -> list[unified_models.Device]:
        """Get devices in unified format from the Tado X API."""
        rooms_and_devices = await self._api_x.get_rooms_and_devices()
        devices_unified = [
            unified_models.Device.from_x(x_device)
            for room in rooms_and_devices.rooms
            for x_device in room.devices
        ]
        devices_unified.extend(
            [
                unified_models.Device.from_x(x_device)
                for x_device in rooms_and_devices.other_devices
            ]
        )
        return devices_unified


def get_unifier_from_generation(
    generation: TadoLine | None, api_x: ApiX, api_v3: ApiV3
) -> DeviceUnifier:
    """Return the correct unifier for the selected Tado generation."""
    if generation == TadoLine.PRE_LINE_X:
        return UnifierV3(api_v3)
    if generation == TadoLine.LINE_X:
        return UnifierX(api_x)
    raise TadoError("Tado Line not set. Cannot get unified devices.")
