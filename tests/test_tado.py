"""Tests for the Python Tado."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientResponse, ClientResponseError
from aioresponses import aioresponses

from tado import (
    Tado,
)
from tado.exceptions import TadoBadRequestError, TadoConnectionError, TadoException
from tests import load_fixture

from .const import TADO_API_URL, TADO_TOKEN_URL


async def test_create_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )
    async with aiohttp.ClientSession() as session:
        tado = Tado(username="username", password="password", session=session)
        await tado.get_me()
        assert not tado.session.closed
        await tado.close()
        assert tado.session.closed


async def test_login_success(responses: aioresponses) -> None:
    """Test login success."""
    responses.get(
        f"{TADO_API_URL}/me",
        status=200,
        body=load_fixture("me.json"),
    )
    async with aiohttp.ClientSession() as session:
        tado = Tado(username="username", password="password", session=session)
        await tado._login()
        assert tado._access_token == "test"
        assert tado._token_expiry > time.time()
        assert tado._refesh_token == "test_token"


async def test_login_timeout(python_tado: Tado, responses: aioresponses) -> None:
    """Test login timeout."""
    responses.post(
        TADO_TOKEN_URL,
        exception=asyncio.TimeoutError(),
    )
    with pytest.raises(TadoConnectionError):
        await python_tado._login()


async def test_login_invalid_content_type(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test login invalid content type."""
    responses.post(
        TADO_TOKEN_URL,
        status=200,
        headers={"content-type": "text/plain"},
        body="Unexpected response",
    )

    with pytest.raises(TadoException):
        await python_tado._login()


async def test_login_client_response_error(
    python_tado: Tado, responses: aioresponses
) -> None:
    """Test login client response error."""
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.raise_for_status.side_effect = ClientResponseError(
        None, None, status=400
    )
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Error message")

    async def mock_post(*args, **kwargs):
        return mock_response

    with patch("aiohttp.ClientSession.post", new=mock_post):
        with pytest.raises(TadoBadRequestError):
            await python_tado._login()
