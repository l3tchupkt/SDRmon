"""
Stream configuration models.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamConfig:
    """Configuration for an IQ stream."""

    frequency: int
    sample_rate: int
    bandwidth: int | None = None
    gain: float | None = None
    center_frequency: int | None = None

    def __post_init__(self) -> None:
        if self.frequency <= 0:
            raise ValueError("Frequency must be > 0")
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be > 0")
        if self.bandwidth is not None and self.bandwidth <= 0:
            raise ValueError("Bandwidth must be > 0")
