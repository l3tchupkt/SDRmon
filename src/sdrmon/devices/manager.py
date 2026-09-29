"""
SDR device manager for discovery and instantiation.
"""

from typing import List

from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.devices.registry import backend_registry
from sdrmon.errors import DeviceNotFoundError


class SDRManager:
    """High-level API for SDR device management."""

    @staticmethod
    def discover() -> List[DeviceInfo]:
        """Discover all connected SDR devices across all backends."""
        devices: List[DeviceInfo] = []
        for backend in backend_registry.all_backends():
            try:
                devices.extend(backend.detect())
            except Exception:
                # Backend failure should not stop discovery for other backends
                pass
        return devices

    @staticmethod
    def open(
        device_info: DeviceInfo | None = None,
        *,
        driver: str | None = None,
        serial: str | None = None,
    ) -> SDRDevice:
        """Open a specific device based on DeviceInfo or constraints."""
        if device_info is not None:
            backend = backend_registry.get_backend(device_info.driver)
            return backend.open(device_info)

        devices = SDRManager.discover()
        for d in devices:
            if driver is not None and d.driver != driver:
                continue
            if serial is not None and d.serial != serial:
                continue
            backend = backend_registry.get_backend(d.driver)
            return backend.open(d)

        raise DeviceNotFoundError("No matching SDR device found.")

    @staticmethod
    def auto() -> SDRDevice:
        """Automatically find and open the first available SDR device."""
        devices = SDRManager.discover()
        if not devices:
            raise DeviceNotFoundError("No SDR devices found.")
        return SDRManager.open(devices[0])
