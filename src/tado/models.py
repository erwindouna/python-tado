"""Models for the Tado API"""
from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class GetMe(DataClassORJSONMixin):
    """GetMe model."""

    name: str = field(metadata=field_options(alias="name"))
    email: str = field(metadata=field_options(alias="email"))
    id: str = field(metadata=field_options(alias="id"))
    username: str = field(metadata=field_options(alias="username"))
    locale: str = field(metadata=field_options(alias="locale"))
    homes: list[Home] = field(metadata=field_options(alias="homes"))


@dataclass
class Home(DataClassORJSONMixin):
    id: int = field(metadata=field_options(alias="id"))
    name: str = field(metadata=field_options(alias="name"))


@dataclass
class DeviceMetadata(DataClassORJSONMixin):
    platform: str = field(metadata=field_options(alias="platform"))
    osVersion: str = field(metadata=field_options(alias="osVersion"))
    model: str = field(metadata=field_options(alias="model"))
    locale: str = field(metadata=field_options(alias="locale"))


@dataclass
class MobileDevice(DataClassORJSONMixin):
    name: str = field(metadata=field_options(alias="name"))
    id: int = field(metadata=field_options(alias="id"))
    deviceMetadata: DeviceMetadata = field(
        metadata=field_options(alias="deviceMetadata")
    )
