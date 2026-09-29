"""
Tests for SDR device manager and registry.
"""

import pytest

from sdrmon.backends.generic.fake import FakeSDRBackend, FakeSDRDevice
from sdrmon.devices.manager import SDRManager
from sdrmon.devices.registry import backend_registry
from sdrmon.errors import DeviceNotFoundError


@pytest.fixture(autouse=True)
def setup_registry():
    backend_registry.clear()
    backend_registry.register(FakeSDRBackend())
    yield
    backend_registry.clear()


def test_discovery():
    devices = SDRManager.discover()
    assert len(devices) == 1
    assert devices[0].driver == "fake"
    assert devices[0].product == "FakeSDR"


def test_auto_open():
    device = SDRManager.auto()
    assert isinstance(device, FakeSDRDevice)


def test_open_specific():
    devices = SDRManager.discover()
    device = SDRManager.open(devices[0])
    assert isinstance(device, FakeSDRDevice)


def test_auto_not_found():
    backend_registry.clear()
    with pytest.raises(DeviceNotFoundError):
        SDRManager.auto()
