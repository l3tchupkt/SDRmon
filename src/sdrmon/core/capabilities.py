"""
Capabilities model for SDRmon.
"""

from dataclasses import dataclass


from typing import List, Optional

@dataclass(frozen=True)
class Capabilities:
    """Represents the capabilities of an SDR device."""

    frequency: bool = False
    sample_rate: bool = False
    gain: bool = False
    bandwidth: bool = False
    frequency_correction: bool = False
    antennas: bool = False
    transmit: bool = False
    bias_tee: bool = False

    frequency_min: Optional[int] = None
    frequency_max: Optional[int] = None
    sample_rates: Optional[List[int]] = None
    gain_values: Optional[List[float]] = None
    bandwidths: Optional[List[int]] = None

    def check_supported(self, feature: str) -> bool:
        return getattr(self, feature, False)
