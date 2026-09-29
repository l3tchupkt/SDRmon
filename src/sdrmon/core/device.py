"""
Device abstraction for SDRmon.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from sdrmon.core.capabilities import Capabilities
from sdrmon.core.stream import IQStream


@dataclass
class DeviceInfo:
    """Information about a discovered or connected SDR device."""

    driver: str
    vendor: str
    product: str
    serial: str | None
    bus: str | None
    usb_vid: int | None
    usb_pid: int | None


class SDRDevice(ABC):
    """Abstract interface for a software-defined radio device."""

    @property
    @abstractmethod
    def info(self) -> DeviceInfo:
        """Get information about this device."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Capabilities:
        """Get the capabilities of this device."""
        ...

    @abstractmethod
    def open(self) -> None:
        """Open the device for use."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the device and release resources."""
        ...

    @abstractmethod
    def set_frequency(self, frequency: int) -> None:
        """Set the center frequency in Hz."""
        ...

    @abstractmethod
    def set_sample_rate(self, sample_rate: int) -> None:
        """Set the sample rate in Hz."""
        ...

    @abstractmethod
    def set_gain(self, gain: float) -> None:
        """Set the gain in dB."""
        ...

    @abstractmethod
    def start_stream(self) -> IQStream:
        """Start streaming IQ samples."""
        ...

    @abstractmethod
    def stop_stream(self) -> None:
        """Stop streaming IQ samples."""
        ...
