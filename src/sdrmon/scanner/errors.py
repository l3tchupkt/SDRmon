"""
Scanner exceptions.
"""


class ScannerError(Exception):
    """Base class for scanner errors."""

    pass


class ScanConfigurationError(ScannerError, ValueError):
    """Raised when scan configuration is invalid."""

    pass


class ScanCancelled(ScannerError):
    """Raised when a scan is explicitly cancelled."""

    pass
