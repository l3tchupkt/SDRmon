"""
Core exception classes for SDRmon.
"""


class SDRmonError(Exception):
    """Base exception for all SDRmon errors."""

    pass


class DeviceNotFoundError(SDRmonError):
    """Raised when an SDR device cannot be found."""

    pass


class DeviceBusyError(SDRmonError):
    """Raised when an SDR device is already in use by another application."""

    pass


class DevicePermissionError(SDRmonError):
    """Raised when permissions are insufficient to access the device."""

    pass


class UnsupportedCapabilityError(SDRmonError):
    """Raised when a requested capability is not supported by the hardware."""

    pass


class StreamError(SDRmonError):
    """Raised when an error occurs during IQ streaming."""

    pass


class BackendError(SDRmonError):
    """Raised when an SDR backend encounters a low-level error."""

    pass


class CaptureError(SDRmonError):
    """Raised when an error occurs during capture."""

    pass


class ConfigurationError(SDRmonError):
    """Raised when configuration is invalid."""

    pass
