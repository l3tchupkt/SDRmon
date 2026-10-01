import pytest

from sdrmon.backends.rtl_sdr.backend import RtlSdrBackend
from sdrmon.core.settings import StreamConfig


@pytest.mark.hardware
def test_rtlsdr_hardware_stream():
    """
    Hardware test for RTL-SDR.
    Requires a physical RTL-SDR device plugged into the machine.
    """
    backend = RtlSdrBackend()
    devices = backend.detect()

    if not devices:
        pytest.skip("No RTL-SDR hardware found")

    device_info = devices[0]
    dev = backend.open(device_info)

    try:
        # Conservative settings
        config = StreamConfig(
            frequency=100_000_000,
            sample_rate=1_000_000,
            gain=None,
        )

        stream = dev.stream(config)

        stream.start()
        block = stream.read()
        stream.stop()

        assert block is not None
        assert block.sample_rate == 1_000_000
        assert block.center_frequency == 100_000_000
        assert len(block.samples) > 0
    finally:
        dev.close()
