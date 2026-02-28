"""Abstract models for interaction with the Tado API, regardless of line."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro.mixins.orjson import DataClassORJSONMixin

from tadoasync import models_v3, models_x


@dataclass
class Device(DataClassORJSONMixin):
    """Device model."""

    device_type: str
    serial: str
    firmware_version: str

    connection_state: bool

    battery_state: str | None  # TODO: Enum

    temperature_offset: float | None = None

    child_lock_enabled: bool | None = None

    @classmethod
    def from_v3(
        cls,
        v3_device: models_v3.Device,
        offset: models_v3.TemperatureOffset | None = None,
    ) -> Device:
        """Create a device from the v3 API."""
        return cls(
            device_type=v3_device.device_type,
            serial=v3_device.serial_no,
            firmware_version=v3_device.current_fw_version,
            temperature_offset=offset.celsius if offset else None,
            connection_state=v3_device.connection_state.value,
            battery_state=v3_device.battery_state,
            child_lock_enabled=v3_device.child_lock_enabled,
        )

    @classmethod
    def from_x(
        cls,
        x_device: models_x.Device,
    ) -> Device:
        """Create a device from the X API."""
        return cls(
            device_type=x_device.type,
            serial=x_device.serial_number,
            firmware_version=x_device.firmware_version,
            connection_state=x_device.connection.state == "CONNECTED",
            battery_state=x_device.battery_state,
            child_lock_enabled=x_device.child_lock_enabled,
        )
