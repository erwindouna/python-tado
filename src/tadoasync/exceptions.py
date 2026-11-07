"""Exceptions for Tado API."""


class TadoError(Exception):
    """Base exception for Tado API."""


class TadoConnectionError(TadoError):
    """Tado connection exception."""


class TadoAuthenticationError(TadoError):
    """Tado authentication exception."""


class TadoServerError(TadoError):
    """Tado server exception."""


class TadoRateLimitError(TadoError):
    """Tado API rate limit (daily quota) exception."""


class TadoBadRequestError(TadoError):
    """Tado bad request exception."""


class TadoForbiddenError(TadoError):
    """Tado forbidden exception."""


class TadoReadingError(TadoError):
    """Tado reading exception."""
