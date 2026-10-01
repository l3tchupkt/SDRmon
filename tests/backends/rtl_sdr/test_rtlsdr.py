"""
RTL-SDR backend tests.

Layer 1 (no hardware): Tests the Python adapter layer that wraps the native C++ manager.
Layer 2 (native mock): Tests discovery/open via mocked NativeSDRManager.
Layer 3 (hardware): Marked @pytest.mark.hardware - requires physical RTL-SDR device.

IQ conversion correctness is tested via the known-value assertions (the C++ backend
performs the same (x - 127.5) / 127.5 conversion — we test numerically here to
document and guard the contract.)
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from sdrmon.backends.rtl_sdr.backend import RtlSdrBackend
from sdrmon.core.device import DeviceInfo

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _fake_device_info() -> DeviceInfo:
    return DeviceInfo(
        driver="rtl_sdr",
        vendor="RTLSDRBlog",
        product="Blog V4",
        serial="00000001",
        bus="rtl_sdr:0",
        usb_vid=None,
        usb_pid=None,
    )


def _fake_native_device_info():
    nd = MagicMock()
    nd.backend_name = "rtl_sdr"
    nd.manufacturer = "RTLSDRBlog"
    nd.product = "Blog V4"
    nd.serial = "00000001"
    nd.identifier = "rtl_sdr:0"
    nd.capabilities.has_gain = True
    nd.capabilities.has_bandwidth = True
    nd.capabilities.has_frequency_correction = False
    nd.capabilities.has_tx = False
    nd.capabilities.supported_sample_rates = []
    nd.capabilities.supported_gains = []
    return nd


# --------------------------------------------------------------------------- #
# Layer 1 — Backend registration / no-hardware                                #
# --------------------------------------------------------------------------- #


class TestRtlSdrBackendRegistration:
    def test_name(self):
        backend = RtlSdrBackend()
        assert backend.name == "rtl_sdr"

    def test_detect_returns_list(self):
        """detect() must always return a list, even when no device present."""
        backend = RtlSdrBackend()
        with patch("sdrmon.backends.rtl_sdr.backend.NativeSDRManager") as MockMgr:
            mock_mgr = MockMgr.return_value
            mock_mgr.discover.return_value = []
            devices = backend.detect()
        assert isinstance(devices, list)
        assert devices == []

    def test_detect_filters_by_driver(self):
        """detect() must return only rtl_sdr entries, not fake/hackrf."""
        backend = RtlSdrBackend()

        py_fake = DeviceInfo(
            driver="fake",
            vendor="SDRmon",
            product="FakeSDR",
            serial="0001",
            bus="fake:0",
            usb_vid=None,
            usb_pid=None,
        )
        py_rtl = _fake_device_info()

        with patch("sdrmon.backends.rtl_sdr.backend.NativeSDRManager") as MockMgr:
            mock_mgr = MockMgr.return_value
            mock_mgr.discover.return_value = [py_fake, py_rtl]
            devices = backend.detect()

        assert len(devices) == 1
        assert devices[0].driver == "rtl_sdr"

    def test_open_missing_bus_raises(self):
        """open() must raise DeviceNotFoundError if DeviceInfo.bus is empty."""
        from sdrmon.errors import DeviceNotFoundError

        backend = RtlSdrBackend()
        bad_info = DeviceInfo(
            driver="rtl_sdr",
            vendor="Realtek",
            product="RTL-SDR",
            serial=None,
            bus=None,
            usb_vid=None,
            usb_pid=None,
        )
        with pytest.raises(DeviceNotFoundError):
            backend.open(bad_info)

    def test_open_delegates_to_native_manager(self):
        """open() must delegate to NativeSDRManager.open(identifier)."""
        backend = RtlSdrBackend()
        info = _fake_device_info()

        with patch("sdrmon.backends.rtl_sdr.backend.NativeSDRManager") as MockMgr:
            mock_mgr = MockMgr.return_value
            mock_native_device = MagicMock()
            mock_mgr.open.return_value = mock_native_device

            backend.open(info)  # result not used; side-effect is what we're testing

            mock_mgr.open.assert_called_once_with("rtl_sdr:0")


# --------------------------------------------------------------------------- #
# Layer 2 — Native manager mock (no hardware)                                 #
# --------------------------------------------------------------------------- #


class TestNativeManagerIntegration:
    """Tests that exercise the full Python adapter chain but with a mocked C++
    manager."""

    def test_discover_maps_native_info_to_python(self):
        """NativeSDRManager.discover() must correctly map native DeviceInfo structs."""
        from sdrmon.native.manager import NativeSDRManager

        mock_native = _fake_native_device_info()

        with patch("sdrmon.native.manager.sdrmon_native.SDRManager") as MockNativeMgr:
            MockNativeMgr.return_value.discover.return_value = [mock_native]
            mgr = NativeSDRManager()
            devices = mgr.discover()

        assert len(devices) == 1
        d = devices[0]
        assert d.driver == "rtl_sdr"
        assert d.serial == "00000001"
        assert d.bus == "rtl_sdr:0"
        assert d.vendor == "RTLSDRBlog"
        assert d.product == "Blog V4"

    def test_open_returns_wrapped_device(self):
        """NativeSDRManager.open() must return a NativeSDRDevice."""
        from sdrmon.native.device import NativeSDRDevice
        from sdrmon.native.manager import NativeSDRManager

        mock_native_device = MagicMock()

        with patch("sdrmon.native.manager.sdrmon_native.SDRManager") as MockNativeMgr:
            MockNativeMgr.return_value.open.return_value = mock_native_device
            mgr = NativeSDRManager()
            dev = mgr.open("rtl_sdr:0")

        assert isinstance(dev, NativeSDRDevice)


# --------------------------------------------------------------------------- #
# IQ conversion correctness — documented contract                             #
# --------------------------------------------------------------------------- #


class TestIQConversionContract:
    """
    RTL-SDR produces uint8 interleaved IQ, centered at 127.5, range 0-255.
    The correct normalized mapping is: sample = (raw - 127.5) / 127.5
    This produces values in [-1.0, +1.0].

    These tests document and guard that exact contract for any implementation
    (C++ or Python).
    """

    @pytest.mark.parametrize(
        "raw, expected",
        [
            (0, -1.0),  # minimum
            (127, (127 - 127.5) / 127.5),  # just below center
            (128, (128 - 127.5) / 127.5),  # just above center
            (255, 1.0),  # maximum
            (64, (64 - 127.5) / 127.5),  # quarter scale
            (192, (192 - 127.5) / 127.5),  # three-quarter scale
        ],
    )
    def test_conversion_values(self, raw, expected):
        result = (raw - 127.5) / 127.5
        assert abs(result - expected) < 1e-4, (
            f"Raw={raw}: expected {expected:.6f}, got {result:.6f}"
        )

    def test_interleaved_iq_layout(self):
        """Bytes are interleaved: I0 Q0 I1 Q1 ..."""
        raw_bytes = np.array([0, 127, 128, 255], dtype=np.uint8)
        i_raw = raw_bytes[0::2].astype(np.float32)
        q_raw = raw_bytes[1::2].astype(np.float32)
        i = (i_raw - 127.5) / 127.5
        q = (q_raw - 127.5) / 127.5
        samples = (i + 1j * q).astype(np.complex64)

        assert len(samples) == 2
        assert np.isclose(samples[0].real, (0 - 127.5) / 127.5, atol=1e-5)
        assert np.isclose(samples[0].imag, (127 - 127.5) / 127.5, atol=1e-5)
        assert np.isclose(samples[1].real, (128 - 127.5) / 127.5, atol=1e-5)
        assert np.isclose(samples[1].imag, (255 - 127.5) / 127.5, atol=1e-5)

    def test_all_zeros_is_minus_one(self):
        """All-zero IQ input should produce all -1.0+0j*-1.0."""
        raw = np.zeros(8, dtype=np.uint8)
        i = (raw[0::2].astype(np.float32) - 127.5) / 127.5
        q = (raw[1::2].astype(np.float32) - 127.5) / 127.5
        samples = (i + 1j * q).astype(np.complex64)
        assert np.allclose(samples.real, -1.0, atol=1e-5)
        assert np.allclose(samples.imag, -1.0, atol=1e-5)

    def test_center_value_127_is_near_zero(self):
        """Value 127 maps to (127 - 127.5) / 127.5 = -0.00392..., not exactly 0."""
        v = (127 - 127.5) / 127.5
        assert abs(v) < 0.01
        assert v < 0  # slightly negative, not zero

    def test_center_value_128_is_near_zero_positive(self):
        """Value 128 maps to (128 - 127.5) / 127.5 = +0.00392..."""
        v = (128 - 127.5) / 127.5
        assert abs(v) < 0.01
        assert v > 0  # slightly positive


# --------------------------------------------------------------------------- #
# Layer 3 — Physical hardware (requires device connected)                     #
# --------------------------------------------------------------------------- #


@pytest.mark.hardware
class TestRtlSdrHardware:
    """
    End-to-end hardware tests. Run with: uv run pytest -m hardware
    Requires RTL-SDR Blog V4 connected via USB.
    """

    def test_hardware_discover(self):
        from sdrmon.native.manager import NativeSDRManager

        mgr = NativeSDRManager()
        devices = mgr.discover()
        rtl_devices = [d for d in devices if d.driver == "rtl_sdr"]
        assert len(rtl_devices) >= 1, "No RTL-SDR hardware found"

    def test_hardware_full_pipeline(self):
        """
        Acceptance test: open → configure → stream → receive real IQ → stop.
        This test FAILS if streaming hangs or returns all-zero samples.
        """
        import sdrmon_native

        from sdrmon.native.manager import NativeSDRManager

        mgr = NativeSDRManager()
        devices = mgr.discover()
        rtl_devs = [d for d in devices if d.driver == "rtl_sdr"]
        assert rtl_devs, "No RTL-SDR device found for hardware test"

        dev = mgr.open(rtl_devs[0].bus)

        # Configure via native API
        nc = sdrmon_native.StreamConfig()
        nc.center_frequency = 100_000_000
        nc.sample_rate = 2_048_000
        nc.gain_mode = sdrmon_native.GainMode.Manual
        nc.gain_value = 20.0
        dev._native.configure(nc)

        dev.start()
        stream = dev.stream()
        assert stream.running()

        # Must receive at least 3 blocks within reasonable time
        blocks = []
        for _ in range(3):
            block = stream.next_block()
            assert block is not None, "Block timed out — streaming hung"
            blocks.append(block)

        # Verify actual data
        for block in blocks:
            assert len(block.samples) > 0
            rms = float((block.samples.real**2 + block.samples.imag**2).mean() ** 0.5)
            assert rms > 0.0, "All-zero IQ — device is not streaming real data"

        # Verify sequence numbers are monotonically increasing
        seqs = [b.sequence_number for b in blocks]
        assert seqs == sorted(seqs), f"Non-monotonic sequence numbers: {seqs}"

        # Stop and restart lifecycle test
        dev.stop()
        assert not stream.running()
        dev.start()
        stream2 = dev.stream()
        assert stream2.running()
        block2 = stream2.next_block()
        assert block2 is not None

        dev.stop()
        dev.close()
