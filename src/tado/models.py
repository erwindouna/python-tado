"""Models for the Tado API"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class GetMe(DataClassORJSONMixin):
    """GetMe model represents the user's profile information."""

    name: str
    email: str
    id: str
    username: str
    locale: str
    homes: list[Home]


@dataclass
class Home(DataClassORJSONMixin):
    """Home model represents the user's home information."""

    id: int
    name: str


@dataclass
class DeviceMetadata(DataClassORJSONMixin):
    """DeviceMetadata model represents the metadata of a device."""

    platform: str
    osVersion: str
    model: str
    locale: str


@dataclass
class MobileDevice(DataClassORJSONMixin):
    """MobileDevice model represents the user's mobile device information."""

    name: str
    id: int
    deviceMetadata: DeviceMetadata


@dataclass
class ConnectionState(DataClassORJSONMixin):
    """ConnectionState model represents the connection state of a device."""

    value: bool
    timestamp: str


@dataclass
class Characteristics(DataClassORJSONMixin):
    """Characteristics model represents the capabilities of a device."""

    capabilities: list[str]


@dataclass
class MountingState(DataClassORJSONMixin):
    """MountingState model represents the mounting state of a device."""

    value: str
    timestamp: str


@dataclass
class Device(DataClassORJSONMixin):
    """Device model represents a device in a zone."""

    deviceType: str
    serialNo: str
    shortSerialNo: str
    currentFwVersion: str
    connectionState: ConnectionState
    characteristics: Characteristics
    inPairingMode: Optional[bool] = None
    mountingState: Optional[MountingState] = None
    mountingStateWithError: Optional[str] = None
    batteryState: Optional[str] = None
    orientation: Optional[str] = None
    childLockEnabled: Optional[bool] = None


@dataclass
class DazzleMode(DataClassORJSONMixin):
    """DazzleMode model represents the dazzle mode settings of a zone."""

    supported: bool
    enabled: bool


@dataclass
class OpenWindowDetection(DataClassORJSONMixin):
    """OpenWindowDetection model represents the open window detection settings of a zone."""

    supported: bool
    enabled: bool
    timeoutInSeconds: int


@dataclass
class Zone(DataClassORJSONMixin):
    """Zone model represents a zone in a home."""

    id: int
    name: str
    type: str
    dateCreated: str
    deviceTypes: list[str]
    devices: list[Device]
    reportAvailable: bool
    showScheduleSetup: bool
    supportsDazzle: bool
    dazzleEnabled: bool
    dazzleMode: DazzleMode
    openWindowDetection: OpenWindowDetection


@dataclass
class Precision(DataClassORJSONMixin):
    celsius: float
    fahrenheit: float


@dataclass
class Temperature(DataClassORJSONMixin):
    celsius: float
    fahrenheit: float
    type: Optional[str] = None
    precision: Optional[Precision] = None
    timestamp: Optional[str] = None


@dataclass
class SolarIntensity(DataClassORJSONMixin):
    percentage: float
    timestamp: str
    type: str


@dataclass
class WeatherState(DataClassORJSONMixin):
    timestamp: str
    type: str
    value: str


@dataclass
class Weather(DataClassORJSONMixin):
    outsideTemperature: Temperature
    solarIntensity: SolarIntensity
    weatherState: WeatherState


@dataclass
class Home_state(DataClassORJSONMixin):
    presence: str
    presenceLocked: bool
    showHomePresenceSwitchButton: Optional[bool] = None
    showSwitchToAutoGeofencingButton: Optional[bool] = None


@dataclass
class TemperatureRange(DataClassORJSONMixin):
    min: float
    max: float
    step: float


@dataclass
class Temperatures(DataClassORJSONMixin):
    celsius: TemperatureRange
    fahrenheit: TemperatureRange


@dataclass
class Capabilities(DataClassORJSONMixin):
    type: str
    temperatures: Temperatures


@dataclass
class TemperatureOffset(DataClassORJSONMixin):
    celsius: float
    fahrenheit: float


@dataclass
class TemperatureSetting(DataClassORJSONMixin):
    type: str
    power: str
    temperature: Temperature


@dataclass
class Overlay(DataClassORJSONMixin):
    type: str
    setting: TemperatureSetting
    termination: dict
    projectedExpiry: Optional[str] = None


@dataclass
class NextScheduleChange(DataClassORJSONMixin):
    start: str
    setting: TemperatureSetting


@dataclass
class Link(DataClassORJSONMixin):
    state: str


@dataclass
class HeatingPower(DataClassORJSONMixin):
    type: str
    percentage: float
    timestamp: str


@dataclass
class Humidity(DataClassORJSONMixin):
    type: str
    percentage: float
    timestamp: str


@dataclass
class SensorDataPoints(DataClassORJSONMixin):
    insideTemperature: Temperature
    humidity: Humidity


@dataclass
class ZoneState(DataClassORJSONMixin):
    tadoMode: str
    geolocationOverride: bool
    geolocationOverrideDisableTime: Optional[str]
    preparation: Optional[str]
    setting: TemperatureSetting
    overlayType: str
    overlay: Overlay
    openWindow: Optional[str]
    nextTimeBlock: dict
    link: Link
    activityDataPoints: dict
    sensorDataPoints: SensorDataPoints
    nextScheduleChange: Optional[NextScheduleChange] = None


@dataclass
class ZoneStates(DataClassORJSONMixin):
    zoneStates: dict[str, ZoneState]
