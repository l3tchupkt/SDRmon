"""
PlutoSDR backend wrapper.
"""

from typing import List

from sdrmon.backends.base import SDRBackend
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.errors import DeviceNotFoundError
from sdrmon.native.manager import NativeSDRManager


class PlutoSDRBackend(SDRBackend):
    """Backend for PlutoSDR devices using native C++ core."""

    @property
    def name(self) -> str:
        return "pluto"

    def detect(self) -> List[DeviceInfo]:
        manager = NativeSDRManager()
        return [d for d in manager.discover() if d.driver == "pluto"]

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        manager = NativeSDRManager()
        if not device_info.bus:
            raise DeviceNotFoundError("Device identifier missing in DeviceInfo.bus")
        return manager.open(device_info.bus)
