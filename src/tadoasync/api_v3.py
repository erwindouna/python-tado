from __future__ import annotations

from typing import TYPE_CHECKING

import orjson

from tadoasync.models_v3 import TemperatureOffset, Zone, Device

if TYPE_CHECKING:
    from tadoasync.tadoasync import Tado


class ApiV3:
    def __init__(self, base: Tado):
        self._base = base

    async def get_zones(self) -> list[Zone]:
        """Get zones."""
        response = await self._base._request(
            uri=f"homes/{self._base._home_id}/zones",
        )
        obj = orjson.loads(response)
        return [Zone.from_dict(zone) for zone in obj]

    async def get_devices(self) -> list[Device]:
        """Get devices."""
        response = await self._base._request(
            uri=f"homes/{self._base._home_id}/devices",
        )
        obj = orjson.loads(response)
        return [Device.from_dict(device) for device in obj]

    async def get_device(self, serial_no: str) -> Device:
        """Get device."""
        response = await self._base._request(
            uri=f"homes/{self._base._home_id}/devices/{serial_no}",
        )
        return Device.from_json(response)

    async def get_device_temperature_offset(self, serial_no: str) -> TemperatureOffset:
        """Get the device temperature offset."""
        response = await self._base._request(f"devices/{serial_no}/temperatureOffset")
        return TemperatureOffset.from_json(response)
