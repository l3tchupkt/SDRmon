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

    device: str
    frequency: int
    sample_rate: int
    gain: Optional[float]
    format: str
    started_at: str
    duration: Optional[float]

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
