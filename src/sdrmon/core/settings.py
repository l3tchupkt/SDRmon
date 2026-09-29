"""
Stream configuration models.
"""

from dataclasses import dataclass


@dataclass
class StreamConfig:
    """Configuration for an IQ stream."""

    frequency: int
    sample_rate: int
    bandwidth: int | None = None
    gain: float | None = None
    center_frequency: int | None = None
