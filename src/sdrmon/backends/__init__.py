"""
Initialization for SDRmon backends.
"""


def initialize_backends() -> None:
    """Register all available backends."""
    from sdrmon.backends.generic.fake import FakeSDRBackend
    from sdrmon.backends.hackrf.backend import HackRFBackend
    from sdrmon.backends.pluto.backend import PlutoSDRBackend
    from sdrmon.backends.rtl_sdr.backend import RtlSdrBackend
    from sdrmon.devices.registry import backend_registry
    from sdrmon.replay.replay import ReplayBackend

    backend_registry.clear()

    # Register core backends
    backend_registry.register(FakeSDRBackend())
    backend_registry.register(RtlSdrBackend())
    backend_registry.register(HackRFBackend())
    backend_registry.register(PlutoSDRBackend())
    backend_registry.register(ReplayBackend())
