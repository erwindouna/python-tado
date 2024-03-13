"""Asynchronous Python client for the Tado API."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Self

import orjson
from aiohttp import ClientResponse, ClientResponseError
from aiohttp.client import ClientSession
from yarl import URL

from tado.const import HttpMethod
from tado.exceptions import (
    TadoAuthenticationError,
    TadoBadRequestError,
    TadoConnectionError,
    TadoError,
    TadoForbiddenError,
)
from tado.models import (
    Capabilities,
    Device,
    GetMe,
    Home_state,
    MobileDevice,
    TemperatureOffset,
    Weather,
    Zone,
    ZoneState,
    ZoneStates,
)

CLIENT_ID = "tado-web-app"
CLIENT_SECRET = "wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc"  # noqa: S105
AUTHORIZATION_BASE_URL = "https://auth.tado.com/oauth/authorize"
TOKEN_URL = "https://auth.tado.com/oauth/token"  # noqa: S105
API_URL = "my.tado.com/api/v2"


@dataclass
class Tado:  # pylint: disable=too-many-instance-attributes
    """Base class for Tado."""

    session: ClientSession | None = None
    request_timeout: int = 10
    _close_session: bool = False

    def __init__(
        self,
        username: str,
        password: str,
        debug: bool | None = None,
        session: ClientSession | None = None,  # pylint: disable=unused-argument # noqa: ARG002
    ) -> None:
        """Initialize the Tado object."""
        self._username: str = username
        self._password: str = password
        self._debug: bool = debug or False
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Referer": "https://app.tado.com/",
        }
        self._access_token: str | None = None
        self._token_expiry: float | None = None
        self._refesh_token: str | None = None
        self._access_headers: dict[str, str] | None = None
        self._home_id: int | None = None
        self._me: GetMe | None = None
        self._auto_geofencing_supported: bool | None = None

    async def _login(self) -> None:
        """Perform login to Tado."""
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "scope": "home.user",
            "username": self._username,
            "password": self._password,
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                request = await self.session.post(url=TOKEN_URL, data=data)
                request.raise_for_status()
        except asyncio.TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError:
            await self.check_request_status(request)

        content_type = request.headers.get("content-type")
        if content_type and "application/json" not in content_type:
            text = await request.text()
            raise TadoError(
                "Unexpected response from Tado. Content-Type: "
                f"{request.headers.get('content-type')}, "
                f"Response body: {text}"
            )

        response = await request.json()
        self._access_token = response["access_token"]
        self._token_expiry = time.time() + float(response["expires_in"])
        self._refesh_token = response["refresh_token"]

        get_me = await self.get_me()
        self._home_id = get_me.homes[0].id

    async def check_request_status(self, request: ClientResponse) -> None:
        """Check the status of the request and raise the proper exception if needed."""
        status_error_mapping = {
            400: TadoBadRequestError(
                "Bad request to Tado. Response body: " + await request.text()
            ),
            500: TadoError(
                "Error "
                + str(request.status)
                + " connecting to Tado. Response body: "
                + await request.text()
            ),
            401: TadoAuthenticationError(
                "Authentication error connecting to Tado. Response body: "
                + await request.text()
            ),
            403: TadoForbiddenError(
                "Forbidden error connecting to Tado. Response body: "
                + await request.text()
            ),
        }

        raise status_error_mapping.get(request.status) or TadoError(
            f"Error {request.status} connecting to Tado. "
            f"Response body: {await request.text()}"
        )

    async def _refresh_auth(self) -> None:
        """Refresh the authentication token."""
        if self._token_expiry is not None and time.time() < self._token_expiry - 30:
            return

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "scope": "home.user",
            "refresh_token": self._refesh_token,
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                request = await self.session.post(url=TOKEN_URL, data=data)
                request.raise_for_status()
        except asyncio.TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError:
            await self.check_request_status(request)

        response = await request.json()
        self._access_token = response["access_token"]
        self._token_expiry = time.time() + float(response["expires_in"])
        self._refesh_token = response["refresh_token"]

    async def get_me(self) -> GetMe:
        """Get the user information."""
        if self._me is None:
            response = await self._request("me")
            self._me = GetMe.from_json(response)
        return self._me

    async def get_devices(self) -> list[Device]:
        """Get the devices."""
        response = await self._request(f"homes/{self._home_id}/devices")
        obj = orjson.loads(response)
        return [Device.from_dict(device) for device in obj]

    async def get_mobile_devices(self) -> list[MobileDevice]:
        """Get the mobile devices."""
        response = await self._request(f"homes/{self._home_id}/mobileDevices")
        obj = orjson.loads(response)
        return [MobileDevice.from_dict(device) for device in obj]

    async def get_zones(self) -> list[Zone]:
        """Get the zones."""
        response = await self._request(f"homes/{self._home_id}/zones")
        obj = orjson.loads(response)
        return [Zone.from_dict(zone) for zone in obj]

    async def get_zone_states(self) -> list[ZoneStates]:
        """Get the zone states."""
        response = await self._request(f"homes/{self._home_id}/zoneStates")
        obj = orjson.loads(response)
        zone_states = {
            zone_id: ZoneState.from_dict(zone_state_dict)
            for zone_id, zone_state_dict in obj["zoneStates"].items()
        }
        return [ZoneStates(zoneStates=zone_states)]

    async def get_weather(self) -> Weather:
        """Get the weather."""
        response = await self._request(f"homes/{self._home_id}/weather")
        return Weather.from_json(response)

    async def get_home_state(self) -> Home_state:
        """Get the home state."""
        response = await self._request(f"homes/{self._home_id}/state")
        home_state = Home_state.from_json(response)

        self._auto_geofencing_supported = (
            home_state.showSwitchToAutoGeofencingButton or not home_state.presenceLocked
        )

        return home_state

    async def get_capabilities(self, zone: int) -> Capabilities:
        """Get the capabilities."""
        response = await self._request(
            f"homes/{self._home_id}/zones/{zone}/capabilities"
        )
        return Capabilities.from_json(response)

    async def reset_zone_overlay(self, zone: int) -> None:
        """Reset the zone overlay."""
        await self._request(
            f"homes/{self._home_id}/zones/{zone}/overlay", method=HttpMethod.DELETE
        )

    async def set_presence(self, presence: str) -> None:
        """Set the presence."""
        await self._request(
            f"homes/{self._home_id}/presenceLock",
            data={"homePresence": presence},
            method=HttpMethod.PUT,
        )

    async def set_zone_overlay(
        self,
        zone: int,
        overlay_mode: str,
        set_temp: float | None = None,
        duration: int | None = None,
        device_type: str = "HEATING",
        power: str = "ON",
        mode: str | None = None,
        fan_speed: str | None = None,
        swing: str | None = None,
    ) -> None:
        """Set the zone overlay."""
        data = {
            "setting": {
                "type": device_type,
                "power": power,
                **(
                    {"temperature": {"celsius": set_temp}}
                    if set_temp is not None
                    else {}
                ),
                **(
                    {"fanSpeed": fan_speed}
                    if fan_speed is not None and set_temp is not None
                    else {}
                ),
                **(
                    {"swing": swing}
                    if swing is not None and set_temp is not None
                    else {}
                ),
                **({"mode": mode} if mode is not None else {}),
            },
            "termination": {
                "typeSkillBasedApp": overlay_mode,
                **({"durationInSeconds": duration} if duration is not None else {}),
            },
        }
        await self._request(
            f"homes/{self._home_id}/zones/{zone}/overlay",
            data=data,
            method=HttpMethod.PUT,
        )

    async def get_device_info(
        self, serial_no: str, attribute: str
    ) -> TemperatureOffset:
        """Get the device info."""
        response = await self._request(f"devices/{serial_no}/{attribute}")
        return TemperatureOffset.from_json(response)

    async def _request(
        self,
        uri: str,
        data: dict[str, object] | None = None,
        method: HttpMethod = HttpMethod.GET,
    ) -> str:
        """Handle a request to the Tado API."""
        await self._refresh_auth()

        url = URL.build(scheme="https", host=API_URL).joinpath(uri)

        # versienummer nog toevoegen
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        if method == HttpMethod.DELETE:
            headers["Content-Type"] = "text/plain;charset=UTF-8"
        elif method == HttpMethod.PUT:
            headers["Content-Type"] = "application/json;charset=UTF-8"
            headers["Mime-Type"] = "application/json;charset=UTF-8"

        try:
            async with asyncio.timeout(self.request_timeout):
                request = await self.session.request(  # type: ignore[union-attr]
                    method=method.value, url=str(url), headers=headers, json=data
                )
                request.raise_for_status()
        except asyncio.TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError:
            await self.check_request_status(request)

        return await request.text()

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        await self._login()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
