"""
RTL-SDR backend.
"""

from typing import List

from sdrmon.backends.base import SDRBackend
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.errors import DeviceNotFoundError
from sdrmon.native.manager import NativeSDRManager


class RtlSdrBackend(SDRBackend):
    """Backend for RTL-SDR devices using native C++ core."""

    @property
    def name(self) -> str:
        return "rtl_sdr"

    def detect(self) -> List[DeviceInfo]:
        manager = NativeSDRManager()
        return [d for d in manager.discover() if d.driver == "rtl_sdr"]

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        manager = NativeSDRManager()
        # The identifier was mapped to `bus` in NativeSDRManager
        if not device_info.bus:
            raise DeviceNotFoundError("Device identifier missing in DeviceInfo.bus")
        return manager.open(device_info.bus)
