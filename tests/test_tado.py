"""Tests for the Python Tado."""

import asyncio
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientResponse, ClientResponseError, RequestInfo
from aioresponses import CallbackResult, aioresponses
from tadoasync import (
    Tado,
)
from tadoasync.exceptions import (
    TadoAuthenticationError,
    TadoBadRequestError,
    TadoConnectionError,
    TadoError,
    TadoReadingError,
)
from tadoasync.tadoasync import DEVICE_AUTH_URL, DeviceActivationStatus

from syrupy import SnapshotAssertion
from tests import load_fixture

from .const import TADO_API_URL, TADO_EIQ_URL, TADO_TOKEN_URL

AUTH_TOKEN = load_fixture("auth_token.txt")


async def test_create_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )
    async with aiohttp.ClientSession():
        tado = Tado()
        await tado.get_me()
        assert tado._session is not None
        assert not tado._session.closed
        await tado.close()
        assert tado._session.closed


async def test_close_session() -> None:
    """Test not closing the session when the session does not exist."""
    tado = Tado()
    tado._close_session = True
    await tado.close()


async def test_login_success(responses: aioresponses) -> None:
    """Test login success."""
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )
    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        await tado.async_init()
        await tado.device_activation()
        assert tado._access_token == AUTH_TOKEN
        assert tado._token_expiry is not None
        assert tado._token_expiry > time.time()
        assert tado._refresh_token == "test_refresh_token"


async def test_login_success_no_session(responses: aioresponses) -> None:
    """Test login success."""
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )
    async with aiohttp.ClientSession():
        tado = Tado()
        await tado.async_init()
        await tado.device_activation()
        assert tado._access_token == AUTH_TOKEN
        assert tado._token_expiry is not None
        assert tado._token_expiry > time.time()
        assert tado._refresh_token == "test_refresh_token"


async def test_activation_timeout(responses: aioresponses) -> None:
    """Test activation timeout."""
    responses.post(
        DEVICE_AUTH_URL,
        status=200,
        payload={
            "device_code": "XXX_code_XXX",
            "expires_in": 1,
            "interval": 0,
            "user_code": "7BQ5ZQ",
            "verification_uri": "https://login.tado.com/oauth2/device",
            "verification_uri_complete": "https://login.tado.com/oauth2/device?user_code=7BQ5ZQ",
        },
    )
    responses.post(
        TADO_TOKEN_URL,
        status=400,
        payload={"error": "authorization_pending"},
    )

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        await tado.async_init()
        tado._expires_at = datetime.now(UTC) - timedelta(seconds=1)
        with pytest.raises(TadoError, match="User took too long"):
            await tado.device_activation()


async def test_login_device_flow_timeout(responses: aioresponses) -> None:
    """Test timeout during device auth flow."""
    responses._matches.clear()
    responses.post(
        DEVICE_AUTH_URL,
        exception=TimeoutError(),
        repeat=True,
    )

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        with pytest.raises(TadoConnectionError):
            await tado.async_init()


async def test_login_invalid_content_type(responses: aioresponses) -> None:
    """Test login invalid content type."""
    responses._matches.clear()
    responses.post(
        DEVICE_AUTH_URL,
        status=200,
        headers={"content-type": "text/plain"},
        body="Unexpected response",
    )

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        with pytest.raises(TadoError):
            await tado.async_init()


async def test_login_invalid_status() -> None:
    """Test login with non-200 status triggers."""
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.status = 400
    mock_response.headers = {"content-type": "application/json"}
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = AsyncMock(return_value={"error": "bad_request"})
    mock_response.text = AsyncMock(return_value="Unexpected response")

    async def mock_post(*args: Any, **kwargs: Any) -> ClientResponse:  # noqa: ARG001 # pylint: disable=unused-argument
        return mock_response

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        with (
            patch("aiohttp.ClientSession.post", new=mock_post),
            pytest.raises(TadoError),
        ):
            await tado.async_init()


async def test_login_client_response_error() -> None:
    """Test login client response error."""
    mock_request_info = MagicMock(spec=RequestInfo)
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.raise_for_status.side_effect = ClientResponseError(
        mock_request_info, (mock_response,), status=400
    )
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Error message")

    async def mock_post(*args: Any, **kwargs: Any) -> ClientResponse:  # noqa: ARG001 # pylint: disable=unused-argument
        return mock_response

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        with (
            patch("aiohttp.ClientSession.post", new=mock_post),
            pytest.raises(TadoAuthenticationError),
        ):
            await tado.async_init()


async def test_login_client_response_still_pending() -> None:
    """Test login client response error."""
    mock_request_info = MagicMock(spec=RequestInfo)
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.raise_for_status.side_effect = ClientResponseError(
        mock_request_info, (mock_response,), status=400
    )
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="authorization_pending")

    async def mock_post(*args: Any, **kwargs: Any) -> ClientResponse:  # noqa: ARG001 # pylint: disable=unused-argument
        return mock_response

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        with (
            patch("aiohttp.ClientSession.post", new=mock_post),
            pytest.raises(TadoAuthenticationError),
        ):
            await tado.async_init()


async def test_refresh_auth_success(responses: aioresponses) -> None:
    """Test successful refresh of auth token."""
    responses.post(
        TADO_TOKEN_URL,
        status=200,
        payload={
            "access_token": AUTH_TOKEN,
            "expires_in": "3600",
            "refresh_token": "new_test_refresh_token",
        },
        headers={"content-type": "application/json"},
    )
    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        tado._access_token = "old_test_access_token"
        tado._token_expiry = time.time() - 10  # make sure the token is expired
        tado._refresh_token = "old_test_refresh_token"
        await tado._refresh_auth()
        assert tado._access_token == AUTH_TOKEN
        assert tado._token_expiry > time.time()
        assert tado._refresh_token == "test_refresh_token"


async def test_refresh_auth_timeout(python_tado: Tado, responses: aioresponses) -> None:
    """Test timeout during refresh of auth token."""
    responses.post(
        TADO_TOKEN_URL,
        exception=TimeoutError(),
    )
    async with aiohttp.ClientSession():
        python_tado._access_token = "old_test_access_token"
        python_tado._token_expiry = time.time() - 10  # make sure the token is expired
        python_tado._refresh_token = "old_test_refresh_token"
        with pytest.raises(TadoConnectionError):
            await python_tado._refresh_auth()


async def test_refresh_auth_client_response_error(python_tado: Tado) -> None:
    """Test client response error during refresh of auth token."""
    mock_request_info = MagicMock(spec=RequestInfo)
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.raise_for_status.side_effect = ClientResponseError(
        mock_request_info, (mock_response,), status=400, message="Error message"
    )
    mock_response.status = 400
    mock_response.message = "Error message"

    async def mock_post(*args: Any, **kwargs: Any) -> ClientResponse:  # noqa: ARG001 # pylint: disable=unused-argument
        return mock_response

    with patch("aiohttp.ClientSession.post", new=mock_post):
        python_tado._access_token = "old_test_access_token"
        python_tado._token_expiry = time.time() - 10  # make sure the token is expired
        python_tado._refresh_token = "old_test_refresh_token"
        with pytest.raises(TadoBadRequestError):
            await python_tado._refresh_auth()


async def test_device_flow_sets_verification_url(responses: aioresponses) -> None:
    """Test device flow sets verification URL."""
    responses.post(
        DEVICE_AUTH_URL,
        status=200,
        payload={
            "device_code": "XXX",
            "expires_in": 600,
            "interval": 0,
            "user_code": "7BQ5ZQ",
            "verification_uri": "https://login.tado.com/oauth2/device",
        },
    )

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session)
        await tado.login_device_flow()
        assert (
            tado.device_verification_url
            == "https://login.tado.com/oauth2/device?user_code=7BQ5ZQ"
        )


async def test_get_me(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get me."""
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )
    assert await python_tado.get_me() == snapshot


async def test_get_devices(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get devices."""
    responses.get(
        f"{TADO_API_URL}/homes/1/devices",
        status=200,
        body=load_fixture("devices.json"),
    )
    assert await python_tado.get_devices() == snapshot


async def test_get_mobile_devices(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get mobile devices."""
    responses.get(
        f"{TADO_API_URL}/homes/1/mobileDevices",
        status=200,
        body=load_fixture("mobile_devices.json"),
    )
    assert await python_tado.get_mobile_devices() == snapshot


async def test_get_zones(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get zones."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones",
        status=200,
        body=load_fixture("zones.json"),
    )
    assert await python_tado.get_zones() == snapshot


async def test_get_zones_no_owd(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get zones."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones",
        status=200,
        body=load_fixture("zones_no_owd.json"),
    )
    assert await python_tado.get_zones() == snapshot


async def test_get_zone_states_heating_power(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get zone states."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zoneStates",
        status=200,
        body=load_fixture("zone_states_heating_power.json"),
    )
    assert await python_tado.get_zone_states() == snapshot


@pytest.mark.parametrize(
    ("fixture_file"),
    [
        ("zone_states_ac_power.dry.json"),
        ("zone_states_ac_power.fan.json"),
    ],
)
async def test_get_zone_states_ac_power(
    fixture_file: str,
    python_tado: Tado,
    responses: aioresponses,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get zone states."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zoneStates",
        status=200,
        body=load_fixture(fixture_file),
    )
    assert await python_tado.get_zone_states() == snapshot


async def test_get_weather(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get weather."""
    responses.get(
        f"{TADO_API_URL}/homes/1/weather",
        status=200,
        body=load_fixture("weather.json"),
    )
    assert await python_tado.get_weather() == snapshot


async def test_get_home_state(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get home state."""
    responses.get(
        f"{TADO_API_URL}/homes/1/state",
        status=200,
        body=load_fixture("home_state.json"),
    )
    assert await python_tado.get_home_state() == snapshot


async def test_get_capabilities(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get capabilities."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones/1/capabilities",
        status=200,
        body=load_fixture("capabilities.json"),
    )
    assert await python_tado.get_capabilities(1) == snapshot


async def test_get_capabilities_water_heater(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get capabilities."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones/1/capabilities",
        status=200,
        body=load_fixture("capabilities_water_heater.json"),
    )
    assert await python_tado.get_capabilities(1) == snapshot


async def test_get_capabilities_ac(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get capabilities."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones/1/capabilities",
        status=200,
        body=load_fixture("capabilities_ac.json"),
    )
    assert await python_tado.get_capabilities(1) == snapshot


async def test_get_capabilities_ac_new(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get capabilities."""
    responses.get(
        f"{TADO_API_URL}/homes/1/zones/1/capabilities",
        status=200,
        body=load_fixture("capabilities_ac_new.json"),
    )
    assert await python_tado.get_capabilities(1) == snapshot


async def test_reset_zone_overlay_success(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test successful reset of zone overlay."""
    zone_id = 1
    responses.delete(
        f"{TADO_API_URL}/homes/{python_tado._home_id}/zones/{zone_id}/overlay",
        status=204,
    )
    await python_tado.reset_zone_overlay(zone_id)


async def test_set_presence_success(python_tado: Tado, responses: aioresponses) -> None:
    """Test successful setting of presence."""
    presence = "HOME"
    responses.put(
        f"{TADO_API_URL}/homes/{python_tado._home_id}/presenceLock",
        status=204,
        payload={"homePresence": presence},
    )
    await python_tado.set_presence(presence)


# Add this test to cover the DELETE request when presence is AUTO
async def test_set_presence_auto_delete(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test DELETE request when setting presence to AUTO."""
    presence = "AUTO"
    responses.put(
        f"{TADO_API_URL}/homes/{python_tado._home_id}/presenceLock",
        status=204,
        payload={"homePresence": presence},
    )
    responses.delete(
        f"{TADO_API_URL}/homes/{python_tado._home_id}/presenceLock",
        status=204,
    )
    await python_tado.set_presence(presence)


async def test_get_device_info_attribute(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get device info."""
    responses.get(
        f"{TADO_API_URL}/devices/1/temperatureOffset",
        status=200,
        body=load_fixture("device_info_attribute.json"),
    )
    assert await python_tado.get_device_info("1", "temperatureOffset") == snapshot


async def test_get_device_info(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test get device info."""
    responses.get(
        f"{TADO_API_URL}/devices/1/",
        status=200,
        body=load_fixture("device_info.json"),
    )
    assert await python_tado.get_device_info("1") == snapshot


async def test_geofencing_supported(
    python_tado: Tado, responses: aioresponses, snapshot: SnapshotAssertion
) -> None:
    """Test geofencing supported."""
    responses.get(
        f"{TADO_API_URL}/homes/1/state",
        status=200,
        body=load_fixture("home_state.json"),
    )
    assert await python_tado.get_home_state() == snapshot

    python_tado._auto_geofencing_supported = None
    mock_home_state = AsyncMock(return_value=snapshot)
    with patch.object(python_tado, "get_home_state", mock_home_state):
        assert await python_tado.get_auto_geofencing_supported() is None
        mock_home_state.assert_called_once()

    python_tado._auto_geofencing_supported = True
    with patch.object(python_tado, "get_home_state", AsyncMock()) as mock_home_state:
        assert await python_tado.get_auto_geofencing_supported() is True
        mock_home_state.assert_not_called()

    python_tado._auto_geofencing_supported = False
    with patch.object(python_tado, "get_home_state", AsyncMock()) as mock_home_state:
        assert await python_tado.get_auto_geofencing_supported() is False
        mock_home_state.assert_not_called()


async def test_set_zone_overlay_success(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test successful setting of zone overlay."""
    zone = 1
    overlay_mode = "MANUAL"
    set_temp = 20.5
    duration = 3600
    device_type = "HEATING"
    power = "ON"
    mode = "COOL"
    fan_speed = "HIGH"
    swing = "ON"

    responses.put(
        f"{TADO_API_URL}/homes/{python_tado._home_id}/zones/{zone}/overlay",
        status=200,
    )

    await python_tado.set_zone_overlay(
        zone,
        overlay_mode,
        set_temp,
        duration,
        device_type,
        power,
        mode,
        fan_speed,
        swing,
    )


async def test_add_meter_readings_success(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test adding meter readings."""
    responses.post(
        TADO_EIQ_URL,
        body=load_fixture(folder="meter", filename="add_reading_success.json"),
    )
    await python_tado.set_meter_readings(5)


async def test_set_child_lock(python_tado: Tado, responses: aioresponses) -> None:
    """Test setting child lock."""
    device_id = "VA4186719488"
    child_lock = True
    responses.put(
        f"{TADO_API_URL}/devices/{device_id}/childLock",
        status=204,
        payload={"childLockEnabled": child_lock},
    )
    await python_tado.set_child_lock(serial_no=device_id, child_lock=child_lock)


async def test_add_meter_readings_duplicated(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test adding meter readings with duplicate."""
    date = datetime(2023, 10, 1, 12, 0, 0, tzinfo=UTC)
    reading = 5
    responses.post(
        TADO_EIQ_URL,
        body=load_fixture(folder="meter", filename="add_reading_duplicate.json"),
    )
    with pytest.raises(
        TadoReadingError,
        match="Error setting meter reading: "
        "reading already exists for date \\[2024-01-01\\]",
    ):
        await python_tado.set_meter_readings(reading, date)


async def test_request_client_response_error(python_tado: Tado) -> None:
    """Test client response error during request."""
    mock_request_info = MagicMock(spec=RequestInfo)
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.raise_for_status.side_effect = ClientResponseError(
        mock_request_info, (mock_response,), status=400
    )
    mock_response.status = 400
    mock_response.message = "Error message"

    async def mock_get(*args: Any, **kwargs: Any) -> ClientResponse:  # noqa: ARG001 # pylint: disable=unused-argument
        return mock_response

    with (
        patch("aiohttp.ClientSession.request", new=mock_get),
        pytest.raises(TadoBadRequestError),
    ):
        await python_tado._request("me")


fixtures_files = [
    f for f in os.listdir("tests/fixtures/zone_state") if f.endswith(".json")
]


@pytest.mark.parametrize(
    ("fixture_file"),
    fixtures_files,
)
async def test_get_zone_state(
    fixture_file: str,
    python_tado: Tado,
    responses: aioresponses,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get zone states."""
    zone_id = 1
    responses.get(
        f"{TADO_API_URL}/homes/1/zones/{zone_id}/state",
        status=200,
        body=load_fixture(fixture_file, folder="zone_state"),
    )
    assert await python_tado.get_zone_state(zone_id) == snapshot


async def test_get_me_timeout(responses: aioresponses) -> None:
    """Test timeout during get me."""
    responses.post(
        "https://auth.tado.com/oauth/token",
        payload={
            "access_token": AUTH_TOKEN,
            "expires_in": 3600,
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
        },
        status=200,
    )
    responses.post(
        TADO_TOKEN_URL,
        status=200,
        payload={
            "access_token": AUTH_TOKEN,
            "expires_in": 3600,
            "refresh_token": "test_refresh_token",
        },
    )
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )

    # Faking a timeout by sleeping
    async def response_handler(_: str, **_kwargs: Any) -> CallbackResult:  # pylint: disable=unused-argument
        """Response handler for this test."""
        await asyncio.sleep(1)  # Simulate a delay that exceeds the request timeout
        return CallbackResult(body="Goodmorning!")

    responses.get(
        f"{TADO_API_URL}/homes/1/devices",
        body=load_fixture("devices.json"),
        callback=response_handler,
    )

    async with aiohttp.ClientSession() as session:
        tado = Tado(session=session, request_timeout=0)
        await tado.login()
        with pytest.raises(TadoConnectionError):
            await tado.get_devices()
        await tado.close()


async def test_async_init_with_refresh_token() -> None:
    """Cover where refresh token exists and _device_ready is invoked."""
    tado = Tado()
    tado._refresh_token = "existing"

    # Ensure device_activation_status starts NOT_STARTED
    assert tado.device_activation_status == DeviceActivationStatus.NOT_STARTED
    await tado.async_init()
    assert tado.device_activation_status == DeviceActivationStatus.COMPLETED


async def test_login_device_flow_already_in_progress() -> None:
    """Ensure calling login_device_flow again raises TadoError."""
    tado = Tado()
    tado._device_activation_status = DeviceActivationStatus.PENDING
    with pytest.raises(
        TadoError, match="Device activation already in progress or completed"
    ):
        await tado.login_device_flow()
