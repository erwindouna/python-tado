"""Asynchronous Python client for the Tado API."""
from __future__ import annotations
import asyncio

import datetime
from dataclasses import dataclass
from importlib import metadata
import re
import time
from typing import Any, Self
from urllib import request
from aiohttp import ClientConnectorError

from aiohttp.client import ClientSession
from yarl import URL
from tado.const import HttpMethod

from tado.exceptions import TadoAuthenticationError, TadoBadRequestError, TadoConnectionError, TadoException



@dataclass
class Tado:
    """Base class for Tado."""

    session: ClientSession | None = None
    request_timeout: int = 10
    _username: str | None = None
    _password: str | None = None
    _debug: bool = False

    _client_id = "tado-web-app"
    _client_secret = "wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc"
    _authorization_base_url = "https://auth.tado.com/oauth/authorize"
    _token_url = "https://auth.tado.com/oauth/token"
    _api_url = "my.tado.com/api/v2"

    def __init__(self, username: str, password: str, debug: bool = False)-> None:
        """Initialize the Tado object."""
        self._username:str = username
        self._password:str = password
        self._headers:dict = {
            "Content-Type": "application/json",
            "Referer": "https://app.tado.com/",
        }
        self._access_token: str | None = None
        self._token_expiry: float | None = None
        self._refesh_token: str | None = None
        self._access_headers: dict | None = None


    async def _login(self) -> None:
        """Perform login to Tado."""

        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
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
                request = await self.session.post(url=self._token_url, data=data)
        except asyncio.TimeoutError as exception:
            raise TadoConnectionError("Timeout occurred while connecting to Tado.") from exception
        
        if "application/json" not in request.headers.get("content-type"):
            text = await request.text()
            raise TadoException(
                f"Unexpected response from Tado. Content-Type: {request.headers.get('content-type')}, Response body: {text}"
            )

        if request.status != 200:
            if request.status == 401:
                raise TadoBadRequestError("Bad request to Tado.")
            elif request.status == 500:
                text = await request.text()
                raise TadoException(f"Error {request.status} connecting to Tado. Response body: {text}")
            elif request.status == 400:
                raise TadoAuthenticationError("Authentication error connecting to Tado.")
            raise TadoException(f"Error {request.status} connecting to Tado.")
        
        response = await request.json()
        self._access_token = response["access_token"]
        self._token_expiry = (time.time() + float(response["expires_in"]))
        self._refesh_token = response["refresh_token"]       
    

    async def _refresh_auth(self) -> None:
        """Refresh the authentication token."""
        if time.time() < self._token_expiry - 30:
            return
        
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "scope": "home.user",
            "refresh_token": self._refesh_token,
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                request = await self.session.post(url=self._token_url, data=data)
        except asyncio.TimeoutError as exception:
            raise TadoConnectionError("Timeout occurred while connecting to Tado.") from exception
        
        if request.status != 200:
            if request.status == 401:
                raise TadoBadRequestError("Bad request to Tado.")
            elif request.status == 500:
                text = await request.text()
                raise TadoException(f"Error {request.status} connecting to Tado. Response body: {text}")
            elif request.status == 400:
                raise TadoAuthenticationError("Authentication error connecting to Tado.")
            raise TadoException(f"Error {request.status} connecting to Tado.")
        
        response = await request.json()
        self._access_token = response["access_token"]
        self._token_expiry = (time.time() + float(response["expires_in"]))
        self._refesh_token = response["refresh_token"]

    async def get_me(self) -> dict[str, Any]:
        """Get the user information."""
        return await self._request("me")
        
    
    async def _request(self, uri: str, data:dict|None=None,method:str=HttpMethod.GET) -> dict[str, Any]:
        """Handle a request to the Tado API."""
        await self._refresh_auth()

        url = URL.build(scheme="https", host=self._api_url, port=443).joinpath(uri)

        # versienummer nog toevoegen
        headers = {
       
            "Authorization": f"Bearer {self._access_token}",
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                request = await self.session.request(method=method.value, url=str(url), headers=headers, json=data)
        except asyncio.TimeoutError as exception:
            raise TadoConnectionError("Timeout occurred while connecting to Tado.") from exception
        except ClientConnectorError as exception:
            raise TadoConnectionError("Error connecting to Tado.") from exception
        
        if request.status != 200:
            if request.status == 401:
                raise TadoBadRequestError("Bad request to Tado.")
            elif request.status == 500:
                text = await request.text()
                raise TadoException(f"Error {request.status} connecting to Tado. Response body: {text}")
            elif request.status == 400:
                raise TadoAuthenticationError("Authentication error connecting to Tado.")
            raise TadoException(f"Error {request.status} connecting to Tado.")

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The Tado object.
        """
        await self._login()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.
        """
        await self.close()
