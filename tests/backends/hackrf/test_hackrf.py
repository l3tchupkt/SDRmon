from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from sdrmon.backends.hackrf.backend import HackRFBackend, HackRFDevice, HackRFStream
from sdrmon.core.device import DeviceInfo


# Mock the ctypes wrapper fully
@pytest.fixture
def mock_libhackrf(monkeypatch):
    mock_lib = MagicMock()
    mock_lib.HACKRF_ERROR_OK = 0
    # Make sure libhackrf module variable in backend points to this mock
    monkeypatch.setattr("sdrmon.backends.hackrf.backend.libhackrf", mock_lib)
    return mock_lib


def test_hackrf_backend_detect_no_lib(monkeypatch):
    monkeypatch.setattr("sdrmon.backends.hackrf.backend.libhackrf", None)
    backend = HackRFBackend()
    assert backend.detect() == []


def test_hackrf_backend_detect_with_devices(mock_libhackrf):
    mock_libhackrf.hackrf_init.return_value = 0

    # Mock device list
    mock_list_ptr = MagicMock()
    mock_list_ptr.contents.devicecount = 2
    mock_list_ptr.contents.serial_numbers = [
        MagicMock(spec=int), # Just placeholders
        MagicMock(spec=int),
    ]

    with patch("ctypes.string_at", side_effect=[b"0000000000000001", b"0000000000000002"]):
        mock_libhackrf.hackrf_device_list.return_value = mock_list_ptr

        backend = HackRFBackend()
        devices = backend.detect()

        assert len(devices) == 2
        assert devices[0].serial == "0000000000000001"
        assert devices[1].serial == "0000000000000002"


def test_hackrf_device_lifecycle(mock_libhackrf):
    info = DeviceInfo(driver="hackrf", product="HackRF One", vendor="GSG", serial="123", bus=None, usb_vid=None, usb_pid=None)
    dev = HackRFDevice(info)

    mock_libhackrf.hackrf_open_by_serial.return_value = 0

    dev.open()
    mock_libhackrf.hackrf_open_by_serial.assert_called_once()
    mock_libhackrf.hackrf_set_amp_enable.assert_called_once_with(dev._dev, 0)

    dev._dev = MagicMock()
    dev.close()
    mock_libhackrf.hackrf_close.assert_called_once()


def test_hackrf_device_config(mock_libhackrf):
    info = DeviceInfo(driver="hackrf", product="HackRF One", vendor="GSG", serial="123", bus=None, usb_vid=None, usb_pid=None)
    dev = HackRFDevice(info)
    dev._dev = MagicMock() # bypass open

    # Frequency
    mock_libhackrf.hackrf_set_freq.return_value = 0
    dev.set_frequency(433_000_000)
    mock_libhackrf.hackrf_set_freq.assert_called_with(dev._dev, 433_000_000)
    assert dev.get_frequency() == 433_000_000

    with pytest.raises(ValueError):
        dev.set_frequency(100_000) # out of range

    # Sample rate
    mock_libhackrf.hackrf_set_sample_rate.return_value = 0
    dev.set_sample_rate(2_000_000)
    mock_libhackrf.hackrf_set_sample_rate.assert_called_with(dev._dev, 2_000_000.0)
    assert dev.get_sample_rate() == 2_000_000

    # Gain
    mock_libhackrf.hackrf_set_lna_gain.return_value = 0
    mock_libhackrf.hackrf_set_vga_gain.return_value = 0

    dev.set_gain(42.0)
    # LNA should be 40 (max 40, step 8), VGA should be 2
    mock_libhackrf.hackrf_set_lna_gain.assert_called_with(dev._dev, 40)
    mock_libhackrf.hackrf_set_vga_gain.assert_called_with(dev._dev, 2)
    assert dev.get_gain() == 42.0


def test_hackrf_stream(mock_libhackrf):
    info = DeviceInfo(driver="hackrf", product="HackRF One", vendor="GSG", serial="123", bus=None, usb_vid=None, usb_pid=None)
    dev = HackRFDevice(info)
    dev._dev = MagicMock()

    mock_libhackrf.hackrf_start_rx.return_value = 0

    stream = dev.stream()
    assert isinstance(stream, HackRFStream)

    stream.start()
    mock_libhackrf.hackrf_start_rx.assert_called_once()

    # Simulate a callback
    mock_transfer_ptr = MagicMock()
    mock_transfer = mock_transfer_ptr.contents
    mock_transfer.valid_length = 8

    # Provide interleaved I,Q signed bytes
    # [127, 0, -128, 0, 0, 127, 0, -128]
    # => I=[127, -128, 0, 0] Q=[0, 0, 127, -128]
    test_bytes = bytes([127, 0, 128, 0, 0, 127, 0, 128]) # 128 as byte is -128 signed

    with patch("ctypes.string_at", return_value=test_bytes):
        stream._rx_callback(mock_transfer_ptr)

    block = stream.read(timeout=0.1)
    assert len(block.samples) == 4

    # First sample I=127 -> ~0.992
    assert np.isclose(block.samples[0].real, 127.0/128.0)
    assert np.isclose(block.samples[0].imag, 0.0)

    # Second sample I=-128 -> -1.0
    assert np.isclose(block.samples[1].real, -1.0)
    assert np.isclose(block.samples[1].imag, 0.0)

    stream.stop()
    mock_libhackrf.hackrf_stop_rx.assert_called_once_with(dev._dev)
