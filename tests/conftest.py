"""Asynchronous Python client for Tado."""

from collections.abc import AsyncGenerator, Generator

import aiohttp
import pytest
from aioresponses import aioresponses
from tadoasync import Tado

from syrupy import SnapshotAssertion
from tests import load_fixture

from .const import TADO_API_URL, TADO_DEVICE_AUTH_URL, TADO_TOKEN_URL
from .syrupy import TadoSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Tado extension."""
    return snapshot.use_extension(TadoSnapshotExtension)


@pytest.fixture(name="python_tado")
async def client() -> AsyncGenerator[Tado, None]:
    """Return a Tado client."""
    async with (
        aiohttp.ClientSession() as session,
        Tado(
            session=session,
            request_timeout=10,
        ) as tado,
    ):
        await tado.device_activation()
        yield tado


@pytest.fixture(autouse=True)
def _tado_oauth(responses: aioresponses) -> None:
    """Mock the Tado token URL."""
    auth_token = load_fixture("auth_token.txt")

    responses.post(
        TADO_DEVICE_AUTH_URL,
        status=200,
        payload={
            "device_code": "XXX_code_XXX",
            "expires_in": 300,
            "interval": 0,
            "user_code": "7BQ5ZQ",
            "verification_uri": "https://login.tado.com/oauth2/device",
            "verification_uri_complete": "https://login.tado.com/oauth2/device?user_code=7BQ5ZQ",
        },
    )
    responses.post(
        TADO_TOKEN_URL,
        status=200,
        payload={
            "access_token": auth_token,
            "expires_in": 3600,
            "refresh_token": "test_refresh_token",
        },
    )
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )


@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses
