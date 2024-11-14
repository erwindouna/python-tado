"""Asynchronous Python client for the Tado API."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from typing import Self

import orjson
from aiohttp import ClientResponseError
from aiohttp.client import ClientSession
from yarl import URL

from tadoasync.const import (
    CONST_AWAY,
    CONST_FAN_AUTO,
    CONST_FAN_OFF,
    CONST_FAN_SPEED_AUTO,
    CONST_FAN_SPEED_OFF,
    CONST_HORIZONTAL_SWING_OFF,
    CONST_HVAC_COOL,
    CONST_HVAC_HEAT,
    CONST_HVAC_IDLE,
    CONST_HVAC_OFF,
    CONST_LINK_OFFLINE,
    CONST_MODE_OFF,
    CONST_MODE_SMART_SCHEDULE,
    CONST_VERTICAL_SWING_OFF,
    TADO_HVAC_ACTION_TO_MODES,
    TADO_MODES_TO_HVAC_ACTION,
    TYPE_AIR_CONDITIONING,
    HttpMethod,
)
from tadoasync.exceptions import (
    TadoAuthenticationError,
    TadoBadRequestError,
    TadoConnectionError,
    TadoError,
    TadoForbiddenError,
)
from tadoasync.models import (
    Capabilities,
    Device,
    GetMe,
    HomeState,
    MobileDevice,
    SensorDataPoints,
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
TADO_HOST_URL = "my.tado.com"
TADO_API_PATH = "/api/v2"
EIQ_URL = "energy-insights.tado.com/api"
EIQ_HOST_URL = "energy-insights.tado.com"
EIQ_API_PATH = "/api"
VERSION = metadata.version(__package__)


@dataclass
class Tado:  # pylint: disable=too-many-instance-attributes
    """Base class for Tado."""

    def __init__(
        self,
        username: str,
        password: str,
        debug: bool | None = None,
        session: ClientSession | None = None,
        request_timeout: int = 10,
    ) -> None:
        """Initialize the Tado object.

        :param username: Tado account username.
        :param password: Tado account password.
        :param debug: Enable debug logging.
        :param session: HTTP client session.
        :param request_timeout: Timeout for HTTP requests.
        """
        self._username: str = username
        self._password: str = password
        self._debug: bool = debug or False
        self._session = session
        self._request_timeout = request_timeout
        self._close_session = False

        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Referer": "https://app.tado.com/",
        }

        self._access_token: str | None = None
        self._token_expiry: float | None = None
        self._refresh_token: str | None = None
        self._access_headers: dict[str, str] | None = None
        self._home_id: int | None = None
        self._me: GetMe | None = None
        self._auto_geofencing_supported: bool | None = None

    async def login(self) -> None:
        """Perform login to Tado."""
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "scope": "home.user",
            "username": self._username,
            "password": self._password,
        }

        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self._request_timeout):
                request = await self._session.post(url=TOKEN_URL, data=data)
                request.raise_for_status()
        except asyncio.TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError as err:
            await self.check_request_status(err, login=True)

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
        self._refresh_token = response["refresh_token"]

        get_me = await self.get_me()
        self._home_id = get_me.homes[0].id

    async def check_request_status(
        self, response_error: ClientResponseError, *, login: bool = False
    ) -> None:
        """Check the status of the request and raise the proper exception if needed."""
        status_error_mapping = {
            500: TadoError(
                "Error "
                + str(response_error.status)
                + " connecting to Tado. Response body: "
                + response_error.message
            ),
            401: TadoAuthenticationError(
                "Authentication error connecting to Tado. Response body: "
                + response_error.message
            ),
            403: TadoForbiddenError(
                "Forbidden error connecting to Tado. Response body: "
                + response_error.message
            ),
        }

        status_error_mapping[400] = TadoBadRequestError(
            "Bad request to Tado. Response body: " + response_error.message
        )
        if login:
            status_error_mapping[400] = TadoAuthenticationError(
                "Authentication error connecting to Tado. Response body: "
                + response_error.message
            )

        raise status_error_mapping[response_error.status]

    async def _refresh_auth(self) -> None:
        """Refresh the authentication token."""
        if self._token_expiry is not None and time.time() < self._token_expiry - 30:
            return

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "scope": "home.user",
            "refresh_token": self._refresh_token,
        }

        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self._request_timeout):
                request = await self._session.post(url=TOKEN_URL, data=data)
                request.raise_for_status()
        except asyncio.TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError as err:
            await self.check_request_status(err)

        response = await request.json()
        self._access_token = response["access_token"]
        self._token_expiry = time.time() + float(response["expires_in"])
        self._refresh_token = response["refresh_token"]

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
        return [ZoneStates(zone_states=zone_states)]

    async def get_zone_state(self, zone_id: int) -> ZoneState:
        """Get the zone state."""
        response = await self._request(f"homes/{self._home_id}/zones/{zone_id}/state")
        zone_state = ZoneState.from_json(response)
        await self.update_zone_data(zone_state)
        return zone_state

    async def get_weather(self) -> Weather:
        """Get the weather."""
        response = await self._request(f"homes/{self._home_id}/weather")
        return Weather.from_json(response)

    async def get_home_state(self) -> HomeState:
        """Get the home state."""
        response = await self._request(f"homes/{self._home_id}/state")
        home_state = HomeState.from_json(response)
        self._auto_geofencing_supported = (
            home_state.show_switch_to_auto_geofencing_button
            or not home_state.presence_locked
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
        if presence.upper() == "AUTO":
            await self._request(
                f"homes/{self._home_id}/presenceLock",
                method=HttpMethod.DELETE,
            )
        else:
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
        fan_level: str | None = None,
        vertical_swing: str | None = None,
        horizontal_swing: str | None = None,
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
                **({"fanLevel": fan_level} if fan_level is not None else {}),
                **(
                    {"swing": swing}
                    if swing is not None and set_temp is not None
                    else {}
                ),
                **(
                    {"verticalSwing": vertical_swing}
                    if vertical_swing is not None
                    else {}
                ),
                **(
                    {"horizontalSwing": horizontal_swing}
                    if horizontal_swing is not None
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

    async def set_child_lock(self, serial_no: str, child_lock: bool | None) -> None:
        """Set the child lock."""
        if not isinstance(child_lock, bool):
            raise TadoBadRequestError("child_lock must be a boolean")

        await self._request(
            f"devices/{serial_no}/childLock",
            data={"childLockEnabled": child_lock},
            method=HttpMethod.PUT,
        )

    async def set_meter_readings(
        self, date: str | None = None, reading: int = 0
    ) -> str:
        """Set the meter readings."""
        if date is None:
            date = datetime.now(timezone.utc).isoformat()

        payload = {"date": date, "reading": reading}
        response = await self._request(
            endpoint=EIQ_HOST_URL, data=payload, method=HttpMethod.POST
        )
        return json.dumps(response)

    async def _request(
        self,
        uri: str | None = None,
        endpoint: str = API_URL,
        data: dict[str, object] | None = None,
        method: HttpMethod = HttpMethod.GET,
    ) -> str:
        """Handle a request to the Tado API."""
        await self._refresh_auth()

        url = URL.build(scheme="https", host=TADO_HOST_URL, path=TADO_API_PATH)
        if endpoint == EIQ_HOST_URL:
            url = URL.build(scheme="https", host=EIQ_HOST_URL, path=EIQ_API_PATH)

        if uri:
            url = url.joinpath(uri)

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": f"HomeAssistant/{VERSION}",
        }

        if method == HttpMethod.DELETE:
            headers["Content-Type"] = "text/plain;charset=UTF-8"
        elif method == HttpMethod.PUT:
            headers["Content-Type"] = "application/json;charset=UTF-8"
            headers["Mime-Type"] = "application/json;charset=UTF-8"

        try:
            async with asyncio.timeout(self._request_timeout):
                request = await self._session.request(  # type: ignore[union-attr]
                    method=method.value, url=str(url), headers=headers, json=data
                )
                request.raise_for_status()
        except asyncio.TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError as err:
            await self.check_request_status(err)

        return await request.text()

    async def update_zone_data(self, data: ZoneState) -> None:  # pylint: disable=too-many-branches
        """Update the zone data."""
        if (isinstance(data.sensor_data_points, SensorDataPoints)) and (
            hasattr(data, "sensor_data_points")
            and data.sensor_data_points
            and data.sensor_data_points != {}
        ):
            temperature = float(data.sensor_data_points.inside_temperature.celsius)
            data.current_temp = temperature
            data.current_temp_timestamp = (
                data.sensor_data_points.inside_temperature.timestamp
            )
            data.precision = (
                data.sensor_data_points.inside_temperature.precision.celsius
            )

            humidity = float(data.sensor_data_points.humidity.percentage)
            data.current_humidity = humidity
            data.current_humidity_timestamp = data.sensor_data_points.humidity.timestamp

            data.is_away = data.tado_mode == CONST_AWAY
            data.current_hvac_action = CONST_HVAC_OFF

        # Temperature setting will not exist when device is off
        if (
            hasattr(data.setting, "temperature")
            and data.setting.temperature is not None
        ):
            setting = float(data.setting.temperature.celsius)
            data.target_temp = setting

        data.current_fan_speed = None
        data.current_fan_level = None
        # If there is no overlay, the mode will always be
        # "SMART_SCHEDULE"
        data.current_hvac_mode = CONST_MODE_OFF
        data.current_swing_mode = CONST_MODE_OFF
        data.current_vertical_swing_mode = CONST_VERTICAL_SWING_OFF
        data.current_horizontal_swing_mode = CONST_HORIZONTAL_SWING_OFF

        if data.setting.mode is not None:
            # V3 devices use mode
            data.current_hvac_mode = data.setting.mode

        data.current_swing_mode = data.setting.swing
        data.current_vertical_swing_mode = data.setting.vertical_swing
        data.current_horizontal_swing_mode = data.setting.horizontal_swing

        data.power = data.setting.power
        if data.power == "ON":
            data.current_hvac_action = CONST_HVAC_IDLE
            if (
                data.setting.mode is None
                and data.setting.type
                and data.setting.type in TADO_HVAC_ACTION_TO_MODES
            ):
                # V2 devices do not have mode so we have to figure it out from type
                data.current_hvac_mode = TADO_HVAC_ACTION_TO_MODES[data.setting.type]

        # Not all devices have fans
        if data.setting.fan_speed is not None:
            data.current_fan_speed = (
                data.setting.fan_speed
                if hasattr(setting, "fan_speed")
                else CONST_FAN_AUTO
                if data.power == "ON"
                else CONST_FAN_OFF
            )
        elif (
            data.setting.type is not None and data.setting.type == TYPE_AIR_CONDITIONING
        ):
            data.current_fan_speed = (
                CONST_FAN_AUTO if data.power == "ON" else CONST_FAN_OFF
            )

        data.current_fan_level = (
            data.setting.fan_level
            if hasattr(data.setting, "fan_level")
            else CONST_FAN_SPEED_AUTO
            if data.power == "ON"
            else CONST_FAN_SPEED_OFF
        )

        data.open_window_detected = (
            hasattr(data, "open_window_detected")
            and data.open_window_detected is not None
        )

        # Assuming data.open_window is of type 'str | dict[str, str] | None'
        # Never seen it but it could happen to be dict? Validate with Tado Devs
        if data.open_window:
            data.open_window_attr = data.open_window

        if data.activity_data_points.ac_power is not None:
            data.ac_power = data.activity_data_points.ac_power.value
            data.ac_power_timestamp = data.activity_data_points.ac_power.timestamp
            if data.activity_data_points.ac_power.value == "ON" and data.power == "ON":
                # acPower means the unit has power so we need to map the mode
                data.current_hvac_action = TADO_MODES_TO_HVAC_ACTION.get(
                    data.current_hvac_mode, CONST_HVAC_COOL
                )

        if data.activity_data_points.heating_power is not None:
            # This needs to be validated if this is actually in!
            data.heating_power = data.heating_power = (
                data.activity_data_points.heating_power.value
                if data.activity_data_points.heating_power
                else None
            )
            data.heating_power_timestamp = (
                data.activity_data_points.heating_power.timestamp
            )
            data.heating_power_percentage = float(
                data.activity_data_points.heating_power.percentage
                if hasattr(data.activity_data_points.heating_power, "percentage")
                else 0
            )

            # Put the HVAC action to heating if ther's a power percentage and powen = ON
            if data.heating_power_percentage > 0.0 and data.power == "ON":
                data.current_hvac_action = CONST_HVAC_HEAT

        # If there is no overlay, then we are running the smart schedule
        if data.overlay is not None:
            if data.overlay.termination:
                data.overlay_termination_type = data.overlay.termination.type
                data.overlay_termination_timestamp = (
                    data.overlay.termination.projected_expiry
                    if hasattr(data.overlay.termination, "projected_expiry")
                    else None
                )
        else:
            data.current_hvac_mode = CONST_MODE_SMART_SCHEDULE

        data.connection = (
            getattr(data.connection_state, "value", None)
            if hasattr(data, "connection_state")
            else None
        )
        data.available = data.link != CONST_LINK_OFFLINE

        if (
            hasattr(data, "termination_condition")
            and data.termination_condition is not None
        ):
            data.default_overlay_termination_type = (
                data.termination_condition.type
                if data.termination_condition.type
                else None
            )
            data.default_overlay_termination_duration = getattr(
                data.termination_condition, "duration_in_seconds", None
            )

    async def get_auto_geofencing_supported(self) -> bool | None:
        """Return whether the Tado Home supports auto geofencing."""
        if self._auto_geofencing_supported is None:
            await self.get_home_state()

        return self._auto_geofencing_supported

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        await self.login()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
