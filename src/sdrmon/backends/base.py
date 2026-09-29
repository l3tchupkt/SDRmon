"""
Base classes for SDR backends.
"""

from abc import ABC, abstractmethod
from typing import List

from sdrmon.core.device import DeviceInfo, SDRDevice


class SDRBackend(ABC):
    """Abstract interface for a backend provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the backend (e.g. 'rtl_sdr')."""
        ...

    @abstractmethod
    def detect(self) -> List[DeviceInfo]:
        """Detect all connected devices supported by this backend."""
        ...

    @abstractmethod
    def open(self, device_info: DeviceInfo) -> SDRDevice:
        """Open and return a specific device."""
        ...
