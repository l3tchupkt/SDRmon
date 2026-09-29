"""
IQ capture recorder.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from sdrmon.capture.metadata import CaptureMetadata
from sdrmon.core.device import DeviceInfo
from sdrmon.core.samples import IQBlock


class IQRecorder:
    """Records IQ streams to disk with metadata."""

    def __init__(self, iq_path: str | Path, device_info: DeviceInfo | None = None):
        self.iq_path = Path(iq_path)
        self.json_path = self.iq_path.with_suffix(".json")
        self.device_info = device_info
        self._file: BinaryIO | None = None
        self._meta: CaptureMetadata | None = None
        self._samples_written = 0

    def __enter__(self) -> "IQRecorder":
        self._file = open(self.iq_path, "wb")
        return self

    def write(self, block: IQBlock) -> None:
        """Write an IQBlock to the file and initialize metadata if needed."""
        if not self._file:
            raise RuntimeError("Recorder is not open. Use within a context manager.")

        if self._meta is None:
            # Initialize metadata on first block
            dev_str = self.device_info.product if self.device_info else "Unknown SDR"
            self._meta = CaptureMetadata(
                device=dev_str,
                frequency=block.center_frequency,
                sample_rate=block.sample_rate,
                gain=block.gain,
                format="complex64",
                started_at=datetime.now(timezone.utc).isoformat(),
                duration=None,
            )

        # Write samples
        self._file.write(block.samples.tobytes())
        self._samples_written += len(block.samples)

    def close(self) -> None:
        """Close the recorder and write the final metadata."""
        if self._file:
            self._file.close()
            self._file = None

        if self._meta:
            from dataclasses import replace

            # Calculate final duration
            duration = self._samples_written / self._meta.sample_rate
            self._meta = replace(self._meta, duration=duration)
            self._meta.save(self.json_path)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.close()
