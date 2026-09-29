"""
Backend registry for SDRmon.
"""

from typing import Dict, List

from sdrmon.backends.base import SDRBackend


class BackendRegistry:
    """Registry of available SDR backends."""

    _backends: Dict[str, SDRBackend] = {}

    @classmethod
    def register(cls, backend_instance: SDRBackend) -> None:
        """Register a backend instance."""
        cls._backends[backend_instance.name] = backend_instance

    @classmethod
    def get_backend(cls, name: str) -> SDRBackend:
        """Get a backend by name."""
        if name not in cls._backends:
            raise ValueError(f"Backend '{name}' not found.")
        return cls._backends[name]

    @classmethod
    def all_backends(cls) -> List[SDRBackend]:
        """Get all registered backends."""
        return list(cls._backends.values())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (useful for testing)."""
        cls._backends.clear()


backend_registry = BackendRegistry()
