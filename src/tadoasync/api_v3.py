"""Wrapper for Tado v3 API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson

from tadoasync.models_v3 import Device, TemperatureOffset, Zone

if TYPE_CHECKING:
    from tadoasync.tadoasync import Tado


class ApiV3:
    """Wrapper class for the Tado v3 API."""

    def __init__(self, base: Tado) -> None:
        """Initialize the API wrapper."""
        self._base = base

    async def get_zones(self) -> list[Zone]:
        """Get zones."""
        response = await self._base._request(  # noqa: SLF001
            uri=f"homes/{self._base._home_id}/zones",  # noqa: SLF001
        )
        obj = orjson.loads(response)
        return [Zone.from_dict(zone) for zone in obj]

    async def get_devices(self) -> list[Device]:
        """Get devices."""
        response = await self._base._request(  # noqa: SLF001
            uri=f"homes/{self._base._home_id}/devices",  # noqa: SLF001
        )
        obj = orjson.loads(response)
        return [Device.from_dict(device) for device in obj]

    async def get_device(self, serial_no: str) -> Device:
        """Get device."""
        response = await self._base._request(  # noqa: SLF001
            uri=f"homes/{self._base._home_id}/devices/{serial_no}",  # noqa: SLF001
        )
        return Device.from_json(response)

    async def get_device_temperature_offset(self, serial_no: str) -> TemperatureOffset:
        """Get the device temperature offset."""
        response = await self._base._request(f"devices/{serial_no}/temperatureOffset")  # noqa: SLF001
        return TemperatureOffset.from_json(response)
