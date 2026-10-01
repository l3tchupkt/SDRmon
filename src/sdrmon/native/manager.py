from typing import List

import sdrmon_native

from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice

from .device import NativeSDRDevice


class NativeSDRManager:
    """Wrapper for the native C++ SDRManager."""

    def __init__(self):
        self._native_manager = sdrmon_native.SDRManager()

    def discover(self) -> List[DeviceInfo]:
        native_devices = self._native_manager.discover()
        devices = []
        for nd in native_devices:
            # Convert native capabilities to Python capabilities (informational).
            _caps = Capabilities(
                frequency=True,
                sample_rate=True,
                gain=nd.capabilities.has_gain,
                bandwidth=nd.capabilities.has_bandwidth,
                frequency_correction=nd.capabilities.has_frequency_correction,
                transmit=nd.capabilities.has_tx,
                sample_rates=[
                    int(sr[0]) for sr in nd.capabilities.supported_sample_rates
                ],
                gain_values=nd.capabilities.supported_gains,
            )
            # Create Python DeviceInfo
            info = DeviceInfo(
                driver=nd.backend_name,
                vendor=nd.manufacturer,
                product=nd.product,
                serial=nd.serial,
                bus=nd.identifier,
                usb_vid=None,
                usb_pid=None,
            )
            devices.append(info)
        return devices

    def open(self, identifier: str) -> SDRDevice:
        native_device = self._native_manager.open(identifier)
        return NativeSDRDevice(native_device)
