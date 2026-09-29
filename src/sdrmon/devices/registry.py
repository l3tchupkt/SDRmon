"""
Backend registry for SDRmon.
"""

from typing import Dict, List

from sdrmon.backends.base import SDRBackend


class BackendRegistry:
    """Registry of available SDR backends."""

    def __init__(self) -> None:
        self._backends: Dict[str, SDRBackend] = {}

    def register(self, backend_instance: SDRBackend) -> None:
        """Register a backend instance."""
        if backend_instance.name in self._backends:
            raise ValueError(f"Backend '{backend_instance.name}' already registered.")
        self._backends[backend_instance.name] = backend_instance

    def unregister(self, name: str) -> None:
        """Unregister a backend by name."""
        if name in self._backends:
            del self._backends[name]

    def get_backend(self, name: str) -> SDRBackend:
        """Get a backend by name."""
        if name not in self._backends:
            raise ValueError(f"Backend '{name}' not found.")
        return self._backends[name]

    def all_backends(self) -> List[SDRBackend]:
        """Get all registered backends."""
        return list(self._backends.values())

    def clear(self) -> None:
        """Clear the registry (useful for testing)."""
        self._backends.clear()


backend_registry = BackendRegistry()
