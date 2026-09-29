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

try:
    from rtlsdr import RtlSdr  # type: ignore

    HAVE_RTLSDR = True
except ImportError:
    HAVE_RTLSDR = False
    RtlSdr = Any  # type: ignore


class RtlSdrStream(IQStream):
    """IQ stream using rtlsdr library."""

    def __init__(self, sdr: Any):
        self.sdr = sdr
        self._running = False
        self._seq = 0

    def read(self) -> IQBlock:
        if not self._running:
            raise StopIteration()

        # Read 16384 samples by default
        # Read block synchronously for simplicity in this implementation
        samples = self.sdr.read_samples(16384)

        gain = self.sdr.gain
        block = IQBlock(
            samples=samples.astype(np.complex64),
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
        self._gain: float = 0.0

    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency=True,
            sample_rate=True,
            gain=True,
            bandwidth=False,
        )

    def open(self) -> None:
        if not HAVE_RTLSDR:
            raise RuntimeError("pyrtlsdr is not installed.")

        # Open by serial if available, otherwise by index
        if self._info.serial:
            self._sdr = RtlSdr(serial_number=self._info.serial)  # type: ignore
        else:
            # Simple fallback
            self._sdr = RtlSdr()  # type: ignore

    def close(self) -> None:
        if self._stream:
            self._stream.close()
        if self._sdr:
            self._sdr.close()
            self._sdr = None

    def set_frequency(self, frequency: int) -> None:
        if self._sdr:
            self._sdr.center_freq = frequency
        self._freq = frequency

    def get_frequency(self) -> int:
        return self._freq

    def set_sample_rate(self, sample_rate: int) -> None:
        if self._sdr:
            self._sdr.sample_rate = sample_rate
        self._rate = sample_rate

    def get_sample_rate(self) -> int:
        return self._rate

    def set_gain(self, gain: float) -> None:
        if self._sdr:
            self._sdr.gain = gain
        self._gain = gain

    def get_gain(self) -> float:
        return self._gain

    def stream(self, config: "StreamConfig | None" = None) -> IQStream:
        if not self._sdr:
            raise RuntimeError("Device is not open")
        if config:
            self.set_frequency(config.frequency)
            self.set_sample_rate(config.sample_rate)
            if config.gain is not None:
                self.set_gain(config.gain)
        self._stream = RtlSdrStream(self._sdr)
        return self._stream


class RtlSdrBackend(SDRBackend):
    """Backend for RTL-SDR devices."""

    @property
    def name(self) -> str:
        return "rtl_sdr"

    def detect(self) -> List[DeviceInfo]:
        if not HAVE_RTLSDR:
            return []

        devices: List[DeviceInfo] = []
        try:
            device_count: int = int(RtlSdr.get_device_count())  # type: ignore
            for i in range(device_count):
                serial: str = str(RtlSdr.get_device_serial_addresses()[i])  # type: ignore
                devices.append(
                    DeviceInfo(
                        driver="rtl_sdr",
                        vendor="Realtek",
                        product=f"RTL-SDR Device {i}",
                        serial=serial,
                        bus=None,
                        usb_vid=None,
                        usb_pid=None,
                    )
                )
        except Exception:
            pass

        return devices

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        dev = RtlSdrDevice(device_info)
        dev.open()
        return dev
