"""Exceptions for Tado API."""


class TadoError(Exception):
    """Base exception for Tado API."""


class TadoConnectionError(TadoError):
    """Tado connection exception."""


class TadoAuthenticationError(TadoError):
    """Tado authentication exception."""


class TadoServerError(TadoError):
    """Tado server exception."""


class TadoBadRequestError(TadoError):
    """Tado bad request exception."""


class TadoForbiddenError(TadoError):
    """Tado forbidden exception."""
