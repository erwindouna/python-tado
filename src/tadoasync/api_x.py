"""Wrapper for Tado X API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tadoasync.models_x import RoomsAndDevices

API_URL = "hops.tado.com"

if TYPE_CHECKING:
    from tadoasync.tadoasync import Tado


class ApiX:
    """Wrapper class for the Tado X API."""

    def __init__(self, base: Tado) -> None:
        """Initialize the API wrapper."""
        self._base = base

    async def get_rooms_and_devices(self) -> RoomsAndDevices:
        """Get rooms and devices."""
        response = await self._base._request(  # noqa: SLF001
            endpoint=API_URL,
            uri=f"homes/{self._base._home_id}/roomsAndDevices",  # noqa: SLF001
        )
        return RoomsAndDevices.from_json(response)
