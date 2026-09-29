"""
SDRmon

A terminal-first SDR monitoring and analysis toolkit for Python.
"""

__version__ = "0.1.0"

from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.devices.manager import SDRManager
from sdrmon.devices.registry import backend_registry

__all__ = [
    "SDRManager",
    "backend_registry",
    "DeviceInfo",
    "SDRDevice",
]
