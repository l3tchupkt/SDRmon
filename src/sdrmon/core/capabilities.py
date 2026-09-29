"""
Capabilities model for SDRmon.
"""

from dataclasses import dataclass


@dataclass
class Capabilities:
    """Represents the capabilities of an SDR device."""

    frequency_tuning: bool = False
    sample_rate: bool = False
    gain_control: bool = False
    bandwidth_control: bool = False
    bias_tee: bool = False
    transmit: bool = False
    gps: bool = False

    def check_supported(self, feature: str) -> bool:
        return getattr(self, feature, False)
