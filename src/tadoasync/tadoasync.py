"""Asynchronous Python client for the Tado API."""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import metadata
from typing import Self
from urllib.parse import urlencode

import orjson
from aiohttp import ClientResponseError
from aiohttp.client import ClientSession
from yarl import URL

from tadoasync import models_unified as unified_models
from tadoasync.api_v3 import ApiV3
from tadoasync.api_x import ApiX
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
    INSIDE_TEMPERATURE_MEASUREMENT,
    TADO_HVAC_ACTION_TO_MODES,
    TADO_MODES_TO_HVAC_ACTION,
    TYPE_AIR_CONDITIONING,
    HttpMethod,
    TadoLine,
)
from tadoasync.exceptions import (
    TadoAuthenticationError,
    TadoBadRequestError,
    TadoConnectionError,
    TadoError,
    TadoForbiddenError,
    TadoReadingError,
)
from tadoasync.models_v3 import (
    Capabilities,
    Device,
    GetMe,
    HomeState,
    MobileDevice,
    TemperatureOffset,
    Weather,
    Zone,
    ZoneState,
)

CLIENT_ID = "1bb50063-6b0c-4d11-bd99-387f4a91cc46"
TOKEN_URL = "https://login.tado.com/oauth2/token"  # noqa: S105
DEVICE_AUTH_URL = "https://login.tado.com/oauth2/device_authorize"
API_URL = "my.tado.com/api/v2"
TADO_HOST_URL = "my.tado.com"
TADO_API_PATH = "/api/v2"
EIQ_URL = "energy-insights.tado.com/api"
EIQ_HOST_URL = "energy-insights.tado.com"
EIQ_API_PATH = "/api"
VERSION = metadata.version(__package__)

_LOGGER = logging.getLogger(__name__)


class DeviceActivationStatus(enum.StrEnum):
    """Device Activation Status Enum."""

    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


@dataclass
class Tado:  # pylint: disable=too-many-instance-attributes
    """Base class for Tado."""

    def __init__(
        self,
        refresh_token: str | None = None,
        debug: bool | None = None,
        session: ClientSession | None = None,
        request_timeout: int = 10,
    ) -> None:
        """Initialize the Tado object."""
        self._refresh_token = refresh_token
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
        self._access_headers: dict[str, str] | None = None
        self._home_id: int | None = None
        self._me: GetMe | None = None
        self._auto_geofencing_supported: bool | None = None
        self._tado_line: TadoLine | None = None

        self.api_x = ApiX(self)
        self.api_v3 = ApiV3(self)

        self._user_code: str | None = None
        self._device_verification_url: str | None = None
        self._device_flow_data: dict[str, str] = {}
        self._device_activation_status = DeviceActivationStatus.NOT_STARTED
        self._expires_at: datetime | None = None

        _LOGGER.setLevel(logging.DEBUG if debug else logging.INFO)

    async def async_init(self) -> None:
        """Asynchronous initialization for the Tado object."""
        if self._refresh_token is None:
            self._device_activation_status = await self.login_device_flow()
        else:
            self._device_ready()
            get_me = await self.get_me()
            self._home_id = get_me.homes[0].id

    @property
    def device_activation_status(self) -> DeviceActivationStatus:
        """Return the device activation status."""
        return self._device_activation_status

    @property
    def device_verification_url(self) -> str | None:
        """Return the device verification URL."""
        return self._device_verification_url

    @property
    def refresh_token(self) -> str | None:
        """Return the refresh token."""
        return self._refresh_token

    async def login_device_flow(self) -> DeviceActivationStatus:
        """Login using device flow."""
        if self._device_activation_status != DeviceActivationStatus.NOT_STARTED:
            raise TadoError("Device activation already in progress or completed")

        data = {
            "client_id": CLIENT_ID,
            "scope": "offline_access",
        }

        try:
            async with asyncio.timeout(self._request_timeout):
                session = self._ensure_session()
                request = await session.post(url=DEVICE_AUTH_URL, data=data)
                request.raise_for_status()
        except TimeoutError as err:
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

        if request.status != 200:
            raise TadoError(f"Failed to start device activation flow: {request.status}")

        self._device_flow_data = await request.json()

        user_code = urlencode({"user_code": self._device_flow_data["user_code"]})
        visit_url = f"{self._device_flow_data['verification_uri']}?{user_code}"
        self._user_code = self._device_flow_data["user_code"]
        self._device_verification_url = visit_url

        _LOGGER.info("Please visit the following URL: %s", visit_url)

        expires_in_seconds = float(self._device_flow_data["expires_in"])
        self._expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

        _LOGGER.info(
            "Waiting for user to authorize the device. Expires at %s",
            self._expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

        return DeviceActivationStatus.PENDING

    async def _check_device_activation(self) -> bool:
        if self._expires_at is not None and datetime.timestamp(
            datetime.now(UTC)
        ) > datetime.timestamp(self._expires_at):
            raise TadoError("User took too long to enter key")

        # Await the desired interval, before polling the API again
        await asyncio.sleep(float(self._device_flow_data["interval"]))

        data = {
            "client_id": CLIENT_ID,
            "device_code": self._device_flow_data["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        try:
            async with asyncio.timeout(self._request_timeout):
                session = self._ensure_session()
                request = await session.post(url=TOKEN_URL, data=data)
                if request.status == 400:
                    response = await request.json()
                    if response.get("error") == "authorization_pending":
                        _LOGGER.info("Authorization pending. Continuing polling...")
                        return False
                request.raise_for_status()
        except TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err

        content_type = request.headers.get("content-type")
        if content_type and "application/json" not in content_type:
            text = await request.text()
            raise TadoError(
                "Unexpected response from Tado. Content-Type: "
                f"{request.headers.get('content-type')}, "
                f"Response body: {text}"
            )

        if request.status == 200:
            response = await request.json()
            self._access_token = response["access_token"]
            self._token_expiry = time.time() + float(response["expires_in"])
            self._refresh_token = response["refresh_token"]

            get_me = await self.get_me()
            self._home_id = get_me.homes[0].id

            return True

        raise TadoError(f"Login failed. Reason: {request.reason}")

    async def device_activation(self) -> None:
        """Start the device activation process and get the refresh token."""
        if self._device_activation_status == DeviceActivationStatus.NOT_STARTED:
            raise TadoError(
                "Device activation has not yet started or has already completed"
            )

        while True:
            if await self._check_device_activation():
                break

        self._device_ready()

    def _device_ready(self) -> None:
        """Clear up after device activation."""
        self._user_code = None
        self._device_verification_url = None
        self._device_activation_status = DeviceActivationStatus.COMPLETED

    async def login(self) -> None:
        """Perform login to Tado."""
        data = {
            "client_id": CLIENT_ID,
            "grant_type": "password",
            "scope": "home.user",
        }

        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self._request_timeout):
                request = await self._session.post(url=TOKEN_URL, data=data)
                request.raise_for_status()
        except TimeoutError as err:
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
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        _LOGGER.debug("Refreshing Tado token")

        try:
            async with asyncio.timeout(self._request_timeout):
                session = self._ensure_session()
                request = await session.post(url=TOKEN_URL, data=data)
                request.raise_for_status()
        except TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError as err:
            await self.check_request_status(err)

        response = await request.json()
        self._access_token = response["access_token"]
        self._token_expiry = time.time() + float(response["expires_in"])
        self._refresh_token = response["refresh_token"]

        _LOGGER.debug("Tado token refreshed")

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

    async def get_zone_states(self) -> dict[str, ZoneState]:
        """Get the zone states."""
        response = await self._request(f"homes/{self._home_id}/zoneStates")
        obj = orjson.loads(response)
        zone_states = {
            zone_id: ZoneState.from_dict(zone_state_dict)
            for zone_id, zone_state_dict in obj["zoneStates"].items()
        }

        for zone_state in zone_states.values():
            await self.update_zone_data(zone_state)

        return zone_states

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
        self, serial_no: str, attribute: str | None = None
    ) -> TemperatureOffset | Device:
        """Get the device info."""
        if attribute == "temperatureOffset":
            response = await self._request(f"devices/{serial_no}/{attribute}")
            return TemperatureOffset.from_json(response)

        response = await self._request(f"devices/{serial_no}/")
        return Device.from_json(response)

    async def get_unified_devices(self) -> list[unified_models.Device]:
        """Get devices in a unified format, compatible with both Tado X and v3."""
        if self._tado_line == TadoLine.PRE_LINE_X:
            devices = await self.get_devices()
            devices_unified = []
            if not devices:
                raise TadoError("No devices found for the home")
            for v3_device in devices:
                offset = None
                if (
                    INSIDE_TEMPERATURE_MEASUREMENT
                    in v3_device.characteristics.capabilities
                ):
                    try:
                        offset = await self.api_v3.get_device_temperature_offset(
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
        if self._tado_line == TadoLine.LINE_X:
            rooms_and_devices = await self.api_x.get_rooms_and_devices()
            devices_unified = []
            for room in rooms_and_devices.rooms:
                for x_device in room.devices:
                    devices_unified.append(unified_models.Device.from_x(x_device))
            for x_device in rooms_and_devices.other_devices:
                devices_unified.append(unified_models.Device.from_x(x_device))
            return devices_unified
        raise TadoError("Tado Line not set. Cannot get unified devices.")

    async def set_child_lock(self, serial_no: str, *, child_lock: bool) -> None:
        """Set the child lock."""
        await self._request(
            f"devices/{serial_no}/childLock",
            data={"childLockEnabled": child_lock},
            method=HttpMethod.PUT,
        )

    async def set_meter_readings(
        self, reading: int, date: datetime | None = None
    ) -> None:
        """Set the meter readings."""
        if date is None:
            date = datetime.now(UTC)

        payload = {"date": date.strftime("%Y-%m-%d"), "reading": reading}
        response = await self._request(
            endpoint=EIQ_HOST_URL, data=payload, method=HttpMethod.POST
        )
        data = orjson.loads(response)
        if "message" in data:
            raise TadoReadingError(f"Error setting meter reading: {data['message']}")

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
        elif endpoint != API_URL:
            endpoint_url = (
                endpoint if endpoint.startswith("http") else f"https://{endpoint}"
            )
            url = URL(endpoint_url)

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
                session = self._ensure_session()
                request = await session.request(
                    method=method.value, url=str(url), headers=headers, json=data
                )
                request.raise_for_status()
        except TimeoutError as err:
            raise TadoConnectionError(
                "Timeout occurred while connecting to Tado."
            ) from err
        except ClientResponseError as err:
            await self.check_request_status(err)

        return await request.text()

    async def update_zone_data(self, data: ZoneState) -> None:  # pylint: disable=too-many-branches
        """Update the zone data."""
        if data.sensor_data_points is not None:
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
        # If there is no overlay, the mode will always be "SMART_SCHEDULE"
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

        data.preparation = hasattr(data, "preparation") and data.preparation is not None

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

        # The overlay is active if the current mode is not smart schedule
        data.overlay_active = data.current_hvac_mode != CONST_MODE_SMART_SCHEDULE

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
            data.overlay_active = False  # Default to false if no overlay

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
                data.termination_condition.type or None
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

    def _ensure_session(self) -> ClientSession:
        """Return an active aiohttp ClientSession, creating one if needed."""
        if self._session is None or self._session.closed:
            self._session = ClientSession()
            self._close_session = True
        return self._session

    async def __aenter__(self) -> Self:
        """Async enter."""
        await self.async_init()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
