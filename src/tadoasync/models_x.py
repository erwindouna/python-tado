"""Models for the Tado X API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class DeviceManualControlTermination(DataClassORJSONMixin):
    """DeviceManualControlTermination model represents the manual control termination settings of a device."""

    type: str  # TODO: Enum
    duration_in_seconds: int | None = field(
        metadata=field_options(alias="durationInSeconds")
    )


@dataclass
class Connection(DataClassORJSONMixin):
    """Connection model represents the connection information of a device."""

    state: str


@dataclass
class Device(DataClassORJSONMixin):
    """Device model represents the device information."""

    serial_number: str = field(metadata=field_options(alias="serialNumber"))
    type: str
    firmware_version: str = field(metadata=field_options(alias="firmwareVersion"))
    connection: Connection
    battery_state: str | None = field(
        default=None, metadata=field_options(alias="batteryState")
    )
    temperature_as_measured: float | None = field(
        default=None, metadata=field_options(alias="temperatureAsMeasured")
    )
    temperature_offset: float | None = field(
        default=None, metadata=field_options(alias="temperatureOffset")
    )
    mounting_state: str | None = field(
        default=None, metadata=field_options(alias="mountingState")
    )
    child_lock_enabled: bool | None = field(
        default=None, metadata=field_options(alias="childLockEnabled")
    )


@dataclass
class Room(DataClassORJSONMixin):
    """Room model represents the room information of a home."""

    room_id: int = field(metadata=field_options(alias="roomId"))
    room_name: str = field(metadata=field_options(alias="roomName"))
    device_manual_control_termination: DeviceManualControlTermination = field(
        metadata=field_options(alias="deviceManualControlTermination")
    )
    devices: list[Device]
    zone_controller_assignable: bool = field(
        metadata=field_options(alias="zoneControllerAssignable")
    )
    zone_controllers: list[Any] = field(
        metadata=field_options(alias="zoneControllers")
    )  # TODO: Define ZoneController model
    room_link_available: bool = field(metadata=field_options(alias="roomLinkAvailable"))


@dataclass
class RoomsAndDevices(DataClassORJSONMixin):
    """RoomsAndDevices model represents the rooms and devices information of a home."""

    rooms: list[Room]
    other_devices: list[Device] = field(metadata=field_options(alias="otherDevices"))
