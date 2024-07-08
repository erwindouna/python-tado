"""Models for the Tado API."""
from __future__ import annotations

from dataclasses import dataclass

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
class Device(DataClassORJSONMixin):  # pylint: disable=too-many-instance-attributes
    """Device model represents a device in a zone."""

    deviceType: str
    serialNo: str
    shortSerialNo: str
    currentFwVersion: str
    connectionState: ConnectionState
    characteristics: Characteristics
    inPairingMode: bool | None = None
    mountingState: MountingState | None = None
    mountingStateWithError: str | None = None
    batteryState: str | None = None
    orientation: str | None = None
    childLockEnabled: bool | None = None


@dataclass
class DazzleMode(DataClassORJSONMixin):
    """DazzleMode model represents the dazzle mode settings of a zone."""

    supported: bool
    enabled: bool


@dataclass
class OpenWindowDetection(DataClassORJSONMixin):
    """OpenWindowDetection model represents the open window detection settings."""

    supported: bool
    enabled: bool
    timeoutInSeconds: int


@dataclass
class Zone(DataClassORJSONMixin):  # pylint: disable=too-many-instance-attributes
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
    """Precision model represents the precision of a temperature."""

    celsius: float
    fahrenheit: float


@dataclass
class Temperature(DataClassORJSONMixin):
    """Temperature model represents the temperature in Celsius and Fahrenheit."""

    celsius: float
    fahrenheit: float
    type: str | None = None
    precision: Precision | None = None
    timestamp: str | None = None


@dataclass
class SolarIntensity(DataClassORJSONMixin):
    """SolarIntensity model represents the solar intensity."""

    percentage: float
    timestamp: str
    type: str


@dataclass
class WeatherState(DataClassORJSONMixin):
    """WeatherState model represents the weather state."""

    timestamp: str
    type: str
    value: str


@dataclass
class Weather(DataClassORJSONMixin):
    """Weather model represents the weather information."""

    outsideTemperature: Temperature
    solarIntensity: SolarIntensity
    weatherState: WeatherState


@dataclass
class Home_state(DataClassORJSONMixin):  # noqa: N801
    """Home_state model represents the state of a home."""

    presence: str
    presenceLocked: bool
    showHomePresenceSwitchButton: bool | None = None
    showSwitchToAutoGeofencingButton: bool | None = None


@dataclass
class TemperatureRange(DataClassORJSONMixin):
    """TemperatureRange model represents the range of a temperature."""

    min: float
    max: float
    step: float


@dataclass
class Temperatures(DataClassORJSONMixin):
    """Temperatures model represents the temperatures in Celsius and Fahrenheit."""

    celsius: TemperatureRange
    fahrenheit: TemperatureRange


@dataclass
class Capabilities(DataClassORJSONMixin):
    """Capabilities model represents the capabilities of a zone."""

    type: str
    temperatures: Temperatures


@dataclass
class TemperatureOffset(DataClassORJSONMixin):
    """TemperatureOffset model represents the temperature offset."""

    celsius: float
    fahrenheit: float


@dataclass
class TemperatureSetting(DataClassORJSONMixin):
    """TemperatureSetting model represents the temperature setting."""

    type: str
    power: str
    temperature: Temperature | None = None


@dataclass
class Overlay(DataClassORJSONMixin):
    """Overlay model represents the overlay settings of a zone."""

    type: str
    setting: TemperatureSetting
    termination: dict[str, str]
    projectedExpiry: str | None = None


@dataclass
class NextScheduleChange(DataClassORJSONMixin):
    """NextScheduleChange model represents the next schedule change."""

    start: str
    setting: TemperatureSetting


@dataclass
class Link(DataClassORJSONMixin):
    """Link model represents the link of a zone."""

    state: str


@dataclass
class HeatingPower(DataClassORJSONMixin):
    """HeatingPower model represents the heating power."""

    type: str
    percentage: float
    timestamp: str


@dataclass
class Humidity(DataClassORJSONMixin):
    """Humidity model represents the humidity."""

    type: str
    percentage: float
    timestamp: str


@dataclass
class SensorDataPoints(DataClassORJSONMixin):
    """SensorDataPoints model represents the sensor data points."""

    insideTemperature: Temperature
    humidity: Humidity


@dataclass
class ZoneState(DataClassORJSONMixin):  # pylint: disable=too-many-instance-attributes
    """ZoneState model represents the state of a zone."""

    tadoMode: str
    geolocationOverride: bool
    geolocationOverrideDisableTime: str | None
    preparation: str | None
    setting: TemperatureSetting
    overlayType: str
    overlay: Overlay
    openWindow: str | None
    nextTimeBlock: dict[str, str]
    link: Link
    activityDataPoints: dict[str, str]
    sensorDataPoints: SensorDataPoints
    nextScheduleChange: NextScheduleChange | None = None


@dataclass
class ZoneStates(DataClassORJSONMixin):
    """ZoneStates model represents the states of the zones."""

    zoneStates: dict[str, ZoneState]
