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
from sdrmon.core.settings import StreamConfig
from sdrmon.core.stream import IQStream


class IQReplay(IQStream):
    """Standalone IQ file replayer."""

    def __init__(
        self,
        iq_path: str | Path,
        block_size: int = 8192,
        loop: bool = False,
        rate_control: bool = False,
    ):
        self.iq_path = Path(iq_path)
        if self.iq_path.suffix != ".iq":
            raise ValueError("Replay path must end with .iq")
        self.json_path = self.iq_path.with_suffix(".json")
        self.meta = CaptureMetadata.load(self.json_path)
        self.meta.validate()
        self._stream = ReplayStream(
            self.iq_path,
            self.meta,
            block_size=block_size,
            loop=loop,
            rate_control=rate_control,
        )

    def start(self) -> None:
        self._stream.start()

    def read(self) -> IQBlock:
        return self._stream.read()

    def stop(self) -> None:
        self._stream.stop()

    def close(self) -> None:
        self._stream.close()

    def __iter__(self):
        return self._stream.__iter__()

    def __next__(self) -> IQBlock:
        return self._stream.__next__()

    def __enter__(self) -> "IQReplay":
        self._stream.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self._stream.__exit__(exc_type, exc_val, exc_tb)


class ReplayStream(IQStream):
    """Streams data from an IQ file."""

    def __init__(
        self,
        iq_path: Path,
        meta: CaptureMetadata,
        block_size: int = 8192,
        loop: bool = False,
        rate_control: bool = False,
    ):
        self.iq_path = iq_path
        self.meta = meta
        self.block_size = block_size
        self.loop = loop
        self.rate_control = rate_control
        self._running = False
        self._seq = 0
        self._file = open(self.iq_path, "rb")

    def read(self) -> IQBlock:
        if not self._running:
            raise StopIteration()

        # Read block_size complex samples (each sample is 2x float32 = 8 bytes)
        raw_data = self._file.read(self.block_size * 8)
        if not raw_data:
            if self.loop:
                self._file.seek(0)
                raw_data = self._file.read(self.block_size * 8)
                if not raw_data:
                    self._running = False
                    raise StopIteration()
            else:
                self._running = False
                raise StopIteration()

        samples = np.frombuffer(raw_data, dtype=np.complex64)

        # Simulate timing
        if self.rate_control:
            self._samples_read += len(samples)
            target_time = self._start_time + (
                self._samples_read / self.meta.sample_rate
            )
            now = time.monotonic()
            if target_time > now:
                time.sleep(target_time - now)

        block = IQBlock(
            samples=samples,
            sample_rate=self.meta.sample_rate,
            center_frequency=self.meta.center_frequency,
            gain=self.meta.gain,
            timestamp=time.time(),
            sequence_number=self._seq,
        )
        self._seq += 1
        return block

    def start(self) -> None:
        self._running = True
        self._start_time = time.monotonic()
        self._samples_read = 0

    def stop(self) -> None:
        self._running = False
        if not self._file.closed:
            self._file.close()

    @property
    def position(self) -> int:
        return getattr(self, "_samples_read", 0)

    def close(self) -> None:
        self.stop()

    def __iter__(self):
        self.start()
        return self

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "ReplayStream":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.close()


class ReplayDevice(SDRDevice):
    """A device that replays a capture file."""

    def __init__(self, info: DeviceInfo, iq_path: Path, meta: CaptureMetadata):
        self._info = info
        self.iq_path = iq_path
        self.meta = meta
        self._is_open = False
        self._stream = None
        self.loop = False
        self.rate_control = False

    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency=False,
            sample_rate=False,
            gain=False,
            bandwidth=False,
        )

    def open(self) -> None:
        self._is_open = True

    def close(self) -> None:
        if self._stream:
            self._stream.close()
        self._is_open = False

    def set_frequency(self, frequency: int) -> None:
        pass  # Ignored in replay

    def get_frequency(self) -> int:
        return self.meta.center_frequency

    def set_sample_rate(self, sample_rate: int) -> None:
        pass  # Ignored in replay

    def get_sample_rate(self) -> int:
        return self.meta.sample_rate

    def set_gain(self, gain: float) -> None:
        pass  # Ignored in replay

    def get_gain(self) -> float:
        return self.meta.gain or 0.0

    def stream(self, config: "StreamConfig | None" = None) -> IQStream:
        if not self._is_open:
            raise RuntimeError("Device is not open")
        self._stream = ReplayStream(
            self.iq_path, self.meta, loop=self.loop, rate_control=self.rate_control
        )
        return self._stream


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
        meta.validate()
        # Assume .iq file has same stem
        iq_path = json_path.with_suffix(".iq")

        dev = ReplayDevice(device_info, iq_path, meta)
        dev.open()
        return dev
