"""Exceptions for Tado API."""


class TadoException(Exception):
    """Base exception for Tado API."""


class TadoConnectionError(TadoException):
    """Tado connection exception."""


class TadoAuthenticationError(TadoException):
    """Tado authentication exception."""


class TadoServerError(TadoException):
    """Tado server exception."""


class TadoBadRequestError(TadoException):
    """Tado bad request exception."""


class TadoForbiddenError(TadoException):
    """Tado forbidden exception."""
