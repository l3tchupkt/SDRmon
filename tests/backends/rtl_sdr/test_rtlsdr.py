from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from sdrmon.backends.rtl_sdr.backend import RtlSdrBackend, RtlSdrDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig
from sdrmon.errors import (
    BackendError,
    BackendUnavailableError,
    DeviceBusyError,
    DeviceNotFoundError,
    StreamError,
    UnsupportedCapabilityError,
)


@pytest.fixture
def mock_rtlsdr():
    mock_module = MagicMock()
    with patch(
        "sdrmon.backends.rtl_sdr.backend.get_rtlsdr_module", return_value=mock_module
    ):
        yield mock_module


@pytest.fixture
def mock_no_rtlsdr():
    with patch("sdrmon.backends.rtl_sdr.backend.get_rtlsdr_module", return_value=None):
        yield None


def test_detect_no_library(mock_no_rtlsdr):
    backend = RtlSdrBackend()
    devices = backend.detect()
    assert len(devices) == 0


def test_detect_devices(mock_rtlsdr):
    mock_rtlsdr.RtlSdr.get_device_count.return_value = 2
    mock_rtlsdr.RtlSdr.get_device_serial_addresses.return_value = ["12345", "67890"]

    backend = RtlSdrBackend()
    devices = backend.detect()

    assert len(devices) == 2
    assert devices[0].serial == "12345"
    assert devices[1].serial == "67890"
    assert devices[0].bus == "0"


def test_detect_no_devices(mock_rtlsdr):
    mock_rtlsdr.RtlSdr.get_device_count.return_value = 0

    backend = RtlSdrBackend()
    devices = backend.detect()

    assert len(devices) == 0


def test_detect_malformed(mock_rtlsdr):
    mock_rtlsdr.RtlSdr.get_device_count.side_effect = Exception("Crash!")

    backend = RtlSdrBackend()
    devices = backend.detect()

    assert len(devices) == 0


def test_device_open_close(mock_rtlsdr):
    info = DeviceInfo(
        driver="rtl_sdr",
        vendor="Realtek",
        product="RTL-SDR",
        serial="12345",
        bus="0",
        usb_vid=None,
        usb_pid=None,
    )
    dev = RtlSdrDevice(info)

    dev.open()
    mock_rtlsdr.RtlSdr.assert_called_once_with(serial_number="12345")

    assert dev._sdr is not None
    sdr_instance = dev._sdr

    dev.close()
    sdr_instance.close.assert_called_once()


def test_device_open_unavailable(mock_no_rtlsdr):
    info = DeviceInfo(
        driver="rtl_sdr",
        vendor="Realtek",
        product="RTL-SDR",
        serial=None,
        bus="0",
        usb_vid=None,
        usb_pid=None,
    )
    dev = RtlSdrDevice(info)
    with pytest.raises(BackendUnavailableError):
        dev.open()


def test_device_open_errors(mock_rtlsdr):
    info = DeviceInfo(
        driver="rtl_sdr",
        vendor="Realtek",
        product="RTL-SDR",
        serial=None,
        bus="0",
        usb_vid=None,
        usb_pid=None,
    )
    dev = RtlSdrDevice(info)

    # Test device not found
    mock_rtlsdr.RtlSdr.side_effect = Exception("Device not found")
    with pytest.raises(DeviceNotFoundError):
        dev.open()

    # Test device in use
    mock_rtlsdr.RtlSdr.side_effect = Exception("busy")
    with pytest.raises(DeviceBusyError):
        dev.open()

    # Test generic error
    mock_rtlsdr.RtlSdr.side_effect = Exception("Unknown USB error")
    with pytest.raises(BackendError):
        dev.open()


def test_device_configuration(mock_rtlsdr):
    info = DeviceInfo(
        driver="rtl_sdr",
        vendor="Realtek",
        product="RTL-SDR",
        serial=None,
        bus="0",
        usb_vid=None,
        usb_pid=None,
    )
    dev = RtlSdrDevice(info)

    sdr_instance = MagicMock()
    mock_rtlsdr.RtlSdr.return_value = sdr_instance

    dev.open()

    # Frequency
    dev.set_frequency(100_000_000)
    assert sdr_instance.center_freq == 100_000_000

    # Sample Rate
    dev.set_sample_rate(2_000_000)
    assert sdr_instance.sample_rate == 2_000_000

    # Gain Auto
    dev.set_gain("auto")
    sdr_instance.set_manual_gain_enabled.assert_called_with(False)

    # Gain Manual
    dev.set_gain(20.0)
    sdr_instance.set_manual_gain_enabled.assert_called_with(True)
    assert sdr_instance.gain == 20.0

    # Bandwidth
    sdr_instance.set_bandwidth = MagicMock()
    dev.set_bandwidth(1_000_000)
    sdr_instance.set_bandwidth.assert_called_with(1_000_000)


def test_device_unsupported_bandwidth(mock_rtlsdr):
    info = DeviceInfo(
        driver="rtl_sdr",
        vendor="Realtek",
        product="RTL-SDR",
        serial=None,
        bus="0",
        usb_vid=None,
        usb_pid=None,
    )
    dev = RtlSdrDevice(info)

    sdr_instance = MagicMock()
    del sdr_instance.set_bandwidth
    mock_rtlsdr.RtlSdr.return_value = sdr_instance

    dev.open()
    with pytest.raises(UnsupportedCapabilityError):
        dev.set_bandwidth(1_000_000)


def test_stream_reading(mock_rtlsdr):
    info = DeviceInfo(
        driver="rtl_sdr",
        vendor="Realtek",
        product="RTL-SDR",
        serial=None,
        bus="0",
        usb_vid=None,
        usb_pid=None,
    )
    dev = RtlSdrDevice(info)

    sdr_instance = MagicMock()
    sdr_instance.sample_rate = 2_000_000
    sdr_instance.center_freq = 100_000_000
    sdr_instance.gain = 20.0

    # Mock read_bytes to return unsigned 8-bit bytes
    # [127, 127, 255, 0] -> I=0, Q=0, I=1.0, Q=-1.0
    fake_bytes = bytes([127, 127, 255, 0])
    sdr_instance.read_bytes.return_value = fake_bytes
    mock_rtlsdr.RtlSdr.return_value = sdr_instance

    dev.open()
    config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)
    stream = dev.stream(config)

    stream.start()
    block = stream.read()

    assert block.sample_rate == 2_000_000
    assert block.center_frequency == 100_000_000
    assert block.gain == 20.0
    assert block.sequence_number == 0
    assert block.samples.dtype == np.complex64
    assert len(block.samples) == 2

    # Test error mapping
    sdr_instance.read_bytes.side_effect = Exception("USB Disconnected")
    with pytest.raises(StreamError):
        stream.read()
