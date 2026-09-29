"""
Tests for SpectrumAnalyzer.
"""

from sdrmon.analysis.spectrum import SpectrumAnalyzer
from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig


def test_spectrum_analyzer_tone_detection():
    info = DeviceInfo(
        driver="fake",
        vendor="Fake",
        product="Fake",
        serial="1",
        bus=None,
        usb_pid=None,
        usb_vid=None,
    )

    # 2 MHz sample rate
    dev = FakeSDRDevice(info, seed=42)
    dev.open()

    config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)
    stream = dev.stream(config)
    stream.start()

    block = stream.read()

    analyzer = SpectrumAnalyzer(fft_size=2048, window="hann")
    result = analyzer.process(block)

    stream.close()
    dev.close()

    # tone should be at center_frequency + 100 kHz
    expected_peak = 100_000_000 + 100_000

    # fft size = 2048, sample rate = 2_000_000
    # bin width = 2_000_000 / 2048 = 976.5625 Hz
    # tolerance = 1 bin width
    tolerance = 2_000_000 / 2048

    assert result.peak_frequency is not None
    assert abs(result.peak_frequency - expected_peak) <= tolerance
