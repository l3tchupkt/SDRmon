"""
Replay backend for playing back captured IQ files.
"""

import time
from pathlib import Path
from typing import List

import numpy as np

from sdrmon.backends.base import SDRBackend
from sdrmon.capture.metadata import CaptureMetadata
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.stream import IQStream


class ReplayStream(IQStream):
    """Streams data from an IQ file."""

    def __init__(self, iq_path: Path, meta: CaptureMetadata, block_size: int = 8192):
        self.iq_path = iq_path
        self.meta = meta
        self.block_size = block_size
        self._running = True
        self._seq = 0
        self._file = open(self.iq_path, "rb")

    def read(self) -> IQBlock:
        if not self._running:
            raise StopIteration()

        # Read block_size complex samples (each sample is 2x float32 = 8 bytes)
        raw_data = self._file.read(self.block_size * 8)
        if not raw_data:
            self._running = False
            raise StopIteration()

        samples = np.frombuffer(raw_data, dtype=np.complex64)

        # Simulate timing
        time.sleep(len(samples) / self.meta.sample_rate)

        block = IQBlock(
            samples=samples,
            sample_rate=self.meta.sample_rate,
            center_frequency=self.meta.frequency,
            gain=self.meta.gain,
            timestamp=time.time(),
            sequence_number=self._seq,
        )
        self._seq += 1
        return block

    def stop(self) -> None:
        self._running = False
        if not self._file.closed:
            self._file.close()

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "ReplayStream":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.stop()


class ReplayDevice(SDRDevice):
    """A device that replays a capture file."""

    def __init__(self, info: DeviceInfo, iq_path: Path, meta: CaptureMetadata):
        self._info = info
        self.iq_path = iq_path
        self.meta = meta
        self._is_open = False
        self._stream = None

    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency_tuning=False,
            sample_rate=False,
            gain_control=False,
            bandwidth_control=False,
        )

    def open(self) -> None:
        self._is_open = True

    def close(self) -> None:
        if self._stream:
            self._stream.stop()
        self._is_open = False

    def set_frequency(self, frequency: int) -> None:
        pass  # Ignored in replay

    def set_sample_rate(self, sample_rate: int) -> None:
        pass  # Ignored in replay

    def set_gain(self, gain: float) -> None:
        pass  # Ignored in replay

    def start_stream(self) -> IQStream:
        if not self._is_open:
            raise RuntimeError("Device is not open")
        self._stream = ReplayStream(self.iq_path, self.meta)
        return self._stream

    def stop_stream(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream = None


class ReplayBackend(SDRBackend):
    """Backend for replaying IQ files."""

    def __init__(self):
        self._files: List[Path] = []

    def add_file(self, json_path: str | Path) -> None:
        """Add a capture file to be exposed as a replay device."""
        self._files.append(Path(json_path))

    @property
    def name(self) -> str:
        return "replay"

    def detect(self) -> List[DeviceInfo]:
        devices: List[DeviceInfo] = []
        for p in self._files:
            devices.append(
                DeviceInfo(
                    driver="replay",
                    vendor="SDRmon",
                    product=f"Replay: {p.stem}",
                    serial=str(p),
                    bus="virtual",
                    usb_vid=None,
                    usb_pid=None,
                )
            )
        return devices

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        if device_info.serial is None:
            raise ValueError("Serial number is required for ReplayDevice.")
        json_path = Path(device_info.serial)
        meta = CaptureMetadata.load(json_path)
        # Assume .iq file has same stem
        iq_path = json_path.with_suffix(".iq")

        dev = ReplayDevice(device_info, iq_path, meta)
        dev.open()
        return dev
