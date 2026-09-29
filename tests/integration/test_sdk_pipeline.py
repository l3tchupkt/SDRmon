"""
Integration tests for SDK pipeline.
"""

from sdrmon import (
    SDRManager,
    StreamConfig,
    SpectrumAnalyzer,
)


def test_sdk_pipeline():
    from sdrmon.backends import initialize_backends

    initialize_backends()

    # Setup Fake device using manager
    devices = SDRManager.discover()
    fake_info = next((d for d in devices if d.driver == "fake"), None)
    assert fake_info is not None, "Fake backend should be discoverable"

    dev = SDRManager.open(fake_info)

    # Check capabilities
    assert dev.capabilities.frequency
    assert dev.capabilities.sample_rate

    config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)
    analyzer = SpectrumAnalyzer(fft_size=2048)

    with dev.stream(config) as stream:
        block = stream.read()
        result = analyzer.process(block)

        assert result.peak_frequency is not None
        assert 99_000_000 <= result.peak_frequency <= 101_000_000

    dev.close()
