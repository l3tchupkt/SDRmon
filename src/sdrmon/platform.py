"""
Platform diagnostics and environment reporting.
"""

import platform
import sys
from dataclasses import dataclass
from typing import List

import numpy as np

import sdrmon
from sdrmon.devices.registry import backend_registry


@dataclass(frozen=True)
class EnvironmentInfo:
    os: str
    architecture: str
    python_version: str
    numpy_version: str
    sdrmon_version: str
    available_backends: List[str]


def get_environment_info() -> EnvironmentInfo:
    """Get read-only information about the current environment."""
    from sdrmon.backends import initialize_backends

    initialize_backends()

    available = []
    for backend in backend_registry.all_backends():
        try:
            # We consider a backend available if it does not throw on detect
            # or if we explicitly expose it in discovery
            backend.detect()
            available.append(backend.name)
        except Exception:
            pass

    return EnvironmentInfo(
        os=platform.system(),
        architecture=platform.machine(),
        python_version=sys.version,
        numpy_version=np.__version__,
        sdrmon_version=sdrmon.__version__,
        available_backends=available,
    )
