from __future__ import annotations

from typing import TYPE_CHECKING

from tadoasync.models_x import RoomsAndDevices

API_URL = "hops.tado.com"

if TYPE_CHECKING:
    from tadoasync.tadoasync import Tado


class ApiX:
    def __init__(self, base: Tado):
        self._base = base

    async def get_rooms_and_devices(self) -> RoomsAndDevices:
        """Get rooms and devices."""
        response = await self._base._request(
            endpoint=API_URL,
            uri=f"homes/{self._base._home_id}/roomsAndDevices",
        )
        return RoomsAndDevices.from_json(response)
