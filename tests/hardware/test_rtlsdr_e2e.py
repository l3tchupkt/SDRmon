import pytest

from sdrmon.native.manager import NativeSDRManager


@pytest.mark.hardware
def test_physical_rtlsdr_discovery():
    manager = NativeSDRManager()
    devices = manager.discover()
    physical = [d for d in devices if d.driver != "fake"]

    if not physical:
        pytest.skip("No physical RTL-SDR found")

    dev = physical[0]
    assert dev.vendor != ""
    assert dev.product != ""
