"""Tests for abstract cross-line models."""

from __future__ import annotations

import orjson
from tadoasync import models_v3, models_x
from tadoasync.models_unified import Device

from syrupy import SnapshotAssertion
from tests import load_fixture


def test_device_from_v3_with_offset(snapshot: SnapshotAssertion) -> None:
    """Map a v3 device with a temperature offset to the abstract model."""
    v3_devices = orjson.loads(load_fixture("devices.json"))
    v3_device = models_v3.Device.from_dict(v3_devices[1])
    offset = models_v3.TemperatureOffset.from_json(
        load_fixture("device_info_attribute.json")
    )

    device = Device.from_v3(v3_device, offset=offset)

    assert device == snapshot


def test_device_from_v3_without_offset(snapshot: SnapshotAssertion) -> None:
    """Map a v3 device without temperature offset data."""
    v3_devices = orjson.loads(load_fixture("devices.json"))
    v3_device = models_v3.Device.from_dict(v3_devices[0])

    device = Device.from_v3(v3_device)

    assert device == snapshot


def test_device_from_x_connected(snapshot: SnapshotAssertion) -> None:
    """Map a connected X device to the abstract model."""
    rooms_and_devices = models_x.RoomsAndDevices.from_json(
        load_fixture(folder="LINE_X", filename="roomsAndDevices.json")
    )
    x_device = rooms_and_devices.rooms[0].devices[0]

    device = Device.from_x(x_device)

    assert device == snapshot


def test_device_from_x_disconnected(snapshot: SnapshotAssertion) -> None:
    """Map a disconnected X device to the abstract model."""
    rooms_and_devices = models_x.RoomsAndDevices.from_json(
        load_fixture(folder="LINE_X", filename="roomsAndDevices.json")
    )
    x_device = rooms_and_devices.rooms[3].devices[2]

    device = Device.from_x(x_device)

    assert device == snapshot
