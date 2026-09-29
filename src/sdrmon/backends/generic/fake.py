"""
Fake SDR backend and Synthetic Stream for testing.
"""

import time
from typing import List

import numpy as np

from sdrmon.backends.base import SDRBackend
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.settings import StreamConfig
from sdrmon.core.stream import IQStream


class SyntheticStream(IQStream):
    """A stream that generates synthetic IQ data."""

    def __init__(self, sample_rate: int, center_frequency: int, block_size: int = 8192):
        self.sample_rate = sample_rate
        self.center_frequency = center_frequency
        self.block_size = block_size
        self._running = True
        self._seq = 0

    def read(self) -> IQBlock:
        if not self._running:
            raise StopIteration()

        # Simulate time passing to match the sample rate
        time.sleep(self.block_size / self.sample_rate)

        # Generate some noise + a tone
        t = np.arange(self.block_size) / self.sample_rate
        tone_freq = 100_000  # 100 kHz tone

        # Complex tone: exp(j * 2 * pi * f * t)
        signal = np.exp(1j * 2 * np.pi * tone_freq * t).astype(np.complex64)

        # Add noise
        noise = (
            np.random.randn(self.block_size) + 1j * np.random.randn(self.block_size)
        ) * 0.1
        samples = (signal + noise).astype(np.complex64)

        block = IQBlock(
            samples=samples,
            sample_rate=self.sample_rate,
            center_frequency=self.center_frequency,
            gain=0.0,
            timestamp=time.time(),
            sequence_number=self._seq,
        )
        self._seq += 1
        return block

    def stop(self) -> None:
        self._running = False

    def start(self) -> None:
        self._running = True

    def close(self) -> None:
        self.stop()

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "SyntheticStream":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.close()


class FakeSDRDevice(SDRDevice):
    """A fake SDR device that produces synthetic streams."""

    def __init__(self, info: DeviceInfo):
        self._info = info
        self._freq = 100_000_000
        self._rate = 2_000_000
        self._gain = 0.0
        self._stream = None
        self._is_open = False

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
        self._is_open = True

    def close(self) -> None:
        if self._stream:
            self._stream.close()
        self._is_open = False

    def set_frequency(self, frequency: int) -> None:
        self._freq = frequency

    def get_frequency(self) -> int:
        return self._freq

    def set_sample_rate(self, sample_rate: int) -> None:
        self._rate = sample_rate

    def get_sample_rate(self) -> int:
        return self._rate

    def set_gain(self, gain: float) -> None:
        self._gain = gain

    def get_gain(self) -> float:
        return self._gain

    def stream(self, config: "StreamConfig | None" = None) -> IQStream:
        if not self._is_open:
            raise RuntimeError("Device is not open")
        if config:
            self.set_frequency(config.frequency)
            self.set_sample_rate(config.sample_rate)
            if config.gain is not None:
                self.set_gain(config.gain)
        self._stream = SyntheticStream(self._rate, self._freq)
        return self._stream


class FakeSDRBackend(SDRBackend):
    """Backend for the FakeSDRDevice."""

    @property
    def name(self) -> str:
        return "fake"

    def detect(self) -> List[DeviceInfo]:
        return [
            DeviceInfo(
                driver="fake",
                vendor="SDRmon",
                product="FakeSDR",
                serial="0001",
                bus="virtual",
                usb_vid=None,
                usb_pid=None,
            )
        ]

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        dev = FakeSDRDevice(device_info)
        dev.open()
        return dev
