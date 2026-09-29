import pytest

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.scanner import ScanConfig, Scanner


@pytest.fixture
def fake_device():
    info = DeviceInfo("fake", "Fake", "Fake", "1", None, None, None)
    # Tones at 100.5 MHz and 101.5 MHz
    dev = FakeSDRDevice(info, seed=42, absolute_tones=[100_500_000, 101_500_000])
    dev.open()
    yield dev
    dev.close()


def test_fake_scan_detects_absolute_tones(fake_device):
    scanner = Scanner(fake_device)
    config = ScanConfig(
        start_frequency=100_000_000,
        stop_frequency=102_000_000,
        step=500_000,
        dwell_time=0.01,
        sample_rate=2_000_000,
        settle_time=0.0,
        threshold=5.0,  # 5dB above noise floor
    )

    results = list(scanner.scan(config))

    assert len(results) == 5
    # Expect 100.0, 100.5, 101.0, 101.5, 102.0

    # 100.0 (tone at 100.5 is within its sample_rate/2 range?
    # Sample rate is 2MHz -> +/- 1MHz -> yes, it sees 100.5
    # So 100.0 should detect it
    # But wait, scanner results only give ONE peak.
    # Let's check which specific results actually have `occupied=True`.
    # Since tone is at 100.5MHz, when tuned to 100.5MHz, the peak should be strongly at 100.5MHz.

    # Filter occupied
    occupied = [r for r in results if r.occupied]
    assert len(occupied) > 0

    # Check that peaks align with expected tones
    peaks = [r.peak_frequency for r in occupied]
    # One of the peaks should be very close to 100_500_000
    assert any(abs(p - 100_500_000) < 50_000 for p in peaks)
    assert any(abs(p - 101_500_000) < 50_000 for p in peaks)
