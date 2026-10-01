"""
RTL-SDR backend.
"""

import time
from typing import Any, List, Optional

import numpy as np

from sdrmon.backends.base import SDRBackend
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.settings import StreamConfig
from sdrmon.core.stream import IQStream
from sdrmon.errors import (
    BackendError,
    BackendUnavailableError,
    DeviceBusyError,
    DeviceNotFoundError,
    StreamError,
    UnsupportedCapabilityError,
)

_rtlsdr_module = None
_rtlsdr_init_attempted = False


def get_rtlsdr_module() -> Any:
    global _rtlsdr_module, _rtlsdr_init_attempted
    if _rtlsdr_init_attempted:
        return _rtlsdr_module

    _rtlsdr_init_attempted = True
    try:
        import rtlsdr  # type: ignore

        _rtlsdr_module = rtlsdr
    except ImportError:
        pass
    except Exception:
        pass

    return _rtlsdr_module


class RtlSdrStream(IQStream):
    """IQ stream using rtlsdr library."""

    def __init__(self, sdr: Any):
        self.sdr = sdr
        self._running = False
        self._seq = 0

    def read(self) -> IQBlock:
        if not self._running:
            raise StopIteration()

        try:
            # Read 65536 samples (approx 32ms at 2 MS/s)
            raw_bytes = self.sdr.read_bytes(65536 * 2)
        except Exception as e:
            self._running = False
            raise StreamError(f"RTL-SDR read failed: {e}") from e

        # Explicitly implement the RTL-SDR uint8 interleaved IQ mapping
        raw_data = np.frombuffer(raw_bytes, dtype=np.uint8)

        # RTL-SDR yields unsigned 8-bit integers centered around 127.5
        i_raw = raw_data[0::2].astype(np.float32)
        q_raw = raw_data[1::2].astype(np.float32)

        i = (i_raw - 127.5) / 127.5
        q = (q_raw - 127.5) / 127.5

        samples = (i + 1j * q).astype(np.complex64)

        gain = self.sdr.gain
        block = IQBlock(
            samples=samples,
            sample_rate=int(self.sdr.sample_rate),
            center_frequency=int(self.sdr.center_freq),
            gain=float(gain) if gain != "auto" else None,
            timestamp=time.time(),
            sequence_number=self._seq,
        )
        self._seq += 1
        return block

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def close(self) -> None:
        self.stop()

    def __iter__(self):
        self._running = True
        return self

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "RtlSdrStream":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.close()


class RtlSdrDevice(SDRDevice):
    """RTL-SDR device implementation."""

    def __init__(self, info: DeviceInfo):
        self._info = info
        self._sdr: Any = None
        self._stream: Optional[RtlSdrStream] = None
        self._freq: int = 0
        self._rate: int = 0
        self._gain: float | str = "auto"
        self._bandwidth: int | None = None

    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency=True,
            sample_rate=True,
            gain=True,
            bandwidth=True,
        )

    def open(self) -> None:
        rtlsdr = get_rtlsdr_module()
        if not rtlsdr:
            raise BackendUnavailableError(
                "pyrtlsdr is not installed. Install with `pip install sdrmon[rtlsdr]`."
            )

        if self._sdr is not None:
            return  # Already open

        try:
            if self._info.serial:
                self._sdr = rtlsdr.RtlSdr(serial_number=self._info.serial)
            elif self._info.bus:
                self._sdr = rtlsdr.RtlSdr(device_index=int(self._info.bus))
            else:
                self._sdr = rtlsdr.RtlSdr()
        except Exception as e:
            msg = str(e).lower()
            if "not found" in msg or "no devices" in msg:
                raise DeviceNotFoundError(f"RTL-SDR device not found: {e}") from e
            elif "busy" in msg or "in use" in msg or "access" in msg:
                raise DeviceBusyError(f"RTL-SDR device is busy or in use: {e}") from e
            else:
                raise BackendError(f"Failed to open RTL-SDR: {e}") from e

    def close(self) -> None:
        if self._stream:
            self._stream.close()
            self._stream = None

        if self._sdr:
            try:
                self._sdr.close()
            except Exception:
                pass
            finally:
                self._sdr = None

    def set_frequency(self, frequency: int) -> None:
        if self._sdr:
            try:
                self._sdr.center_freq = frequency
            except Exception as e:
                raise ValueError(f"Failed to set frequency {frequency} Hz: {e}") from e
        self._freq = frequency

    def get_frequency(self) -> int:
        if self._sdr:
            return int(self._sdr.center_freq)
        return self._freq

    def set_sample_rate(self, sample_rate: int) -> None:
        if self._sdr:
            try:
                self._sdr.sample_rate = sample_rate
            except Exception as e:
                raise ValueError(
                    f"Failed to set sample rate {sample_rate} Hz: {e}"
                ) from e
        self._rate = sample_rate

    def get_sample_rate(self) -> int:
        if self._sdr:
            return int(self._sdr.sample_rate)
        return self._rate

    def set_gain(self, gain: float | str) -> None:  # type: ignore
        if self._sdr:
            try:
                if gain == "auto":
                    self._sdr.set_manual_gain_enabled(False)
                else:
                    self._sdr.set_manual_gain_enabled(True)
                    self._sdr.gain = float(gain)
            except Exception as e:
                raise ValueError(f"Failed to set gain {gain}: {e}") from e
        self._gain = gain

    def get_gain(self) -> float | str:  # type: ignore
        if self._sdr:
            g = self._sdr.gain
            if g == "auto":
                return g
            return float(g)
        return self._gain

    def set_bandwidth(self, bandwidth: int) -> None:
        if self._sdr:
            try:
                if hasattr(self._sdr, "set_bandwidth"):
                    self._sdr.set_bandwidth(bandwidth)
                else:
                    raise UnsupportedCapabilityError(
                        "Bandwidth control is not supported by this tuner."
                    )
            except Exception as e:
                if isinstance(e, UnsupportedCapabilityError):
                    raise
                raise ValueError(f"Failed to set bandwidth {bandwidth} Hz: {e}") from e
        self._bandwidth = bandwidth

    def stream(self, config: "StreamConfig | None" = None) -> IQStream:
        if not self._sdr:
            raise RuntimeError("Device is not open")

        if self._stream and self._stream._running:
            raise DeviceBusyError("Stream is already running on this device.")

        if config:
            self.set_frequency(config.frequency)
            self.set_sample_rate(config.sample_rate)
            if config.gain is not None:
                self.set_gain(config.gain)
            if config.bandwidth is not None:
                self.set_bandwidth(config.bandwidth)

        self._stream = RtlSdrStream(self._sdr)
        return self._stream


class RtlSdrBackend(SDRBackend):
    """Backend for RTL-SDR devices."""

    @property
    def name(self) -> str:
        return "rtl_sdr"

    def detect(self) -> List[DeviceInfo]:
        rtlsdr = get_rtlsdr_module()
        if not rtlsdr:
            return []

        devices: List[DeviceInfo] = []
        try:
            device_count: int = int(rtlsdr.RtlSdr.get_device_count())
        except Exception:
            return []

        if device_count == 0:
            return []

        try:
            serials = rtlsdr.RtlSdr.get_device_serial_addresses()
        except Exception:
            serials = []

        for i in range(device_count):
            serial = str(serials[i]) if i < len(serials) else None
            devices.append(
                DeviceInfo(
                    driver="rtl_sdr",
                    vendor="Realtek",
                    product="RTL-SDR",
                    serial=serial,
                    bus=str(i),
                    usb_vid=None,
                    usb_pid=None,
                )
            )

        return devices

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        dev = RtlSdrDevice(device_info)
        dev.open()
        return dev
