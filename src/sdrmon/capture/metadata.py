"""
Metadata for IQ captures.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CaptureMetadata:
    """Metadata describing an IQ capture."""

    format: str = "sdrmon-iq"
    version: int = 1
    sample_format: str = "complex64"
    sample_rate: int = 0
    center_frequency: int = 0
    gain: Optional[float] = None
    backend: str = "unknown"
    device: str = "Unknown"
    started_at: str = ""
    duration: Optional[float] = None
    samples: int = 0

    def validate(self) -> None:
        """Validate the metadata schema."""
        if self.format != "sdrmon-iq":
            raise ValueError(f"Invalid capture format: {self.format}")
        if self.version > 1:
            raise ValueError(f"Unsupported capture version: {self.version}")
        if self.sample_format != "complex64":
            raise ValueError(f"Unsupported sample format: {self.sample_format}")
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")

    def save(self, path: Path | str) -> None:
        """Save metadata to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: Path | str) -> "CaptureMetadata":
        """Load metadata from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
