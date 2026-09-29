import time

import pytest

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.scanner import ScanConfig, Scanner


@pytest.fixture
def fake_device():
    info = DeviceInfo("fake", "Fake", "Fake", "1", None, None, None)
    dev = FakeSDRDevice(info, seed=42)
    dev.open()
    yield dev
    dev.close()


def test_scanner_basic(fake_device):
    scanner = Scanner(fake_device)
    config = ScanConfig(
        start_frequency=100_000_000,
        stop_frequency=101_000_000,
        step=500_000,
        dwell_time=0.01,
        sample_rate=2_000_000,
        settle_time=0.01,
    )

    results = list(scanner.scan(config))
    # Should scan 100.0, 100.5, 101.0
    assert len(results) == 3
    assert results[0].frequency == 100_000_000
    assert results[1].frequency == 100_500_000
    assert results[2].frequency == 101_000_000


def test_scanner_cancellation(fake_device):
    scanner = Scanner(fake_device)
    config = ScanConfig(
        start_frequency=100_000_000,
        stop_frequency=110_000_000,
        step=500_000,
        dwell_time=0.1,
        sample_rate=2_000_000,
    )

    results = []
    for res in scanner.scan(config):
        results.append(res)
        if len(results) == 2:
            scanner.cancel()

    assert len(results) == 2


def test_scanner_double_start(fake_device):
    scanner = Scanner(fake_device)
    config = ScanConfig(
        start_frequency=100_000_000,
        stop_frequency=101_000_000,
        step=500_000,
        dwell_time=0.01,
        sample_rate=2_000_000,
    )

    # We can't really double start easily unless we use threads since scan() is synchronous.
    # But we can try to start while scanning is active if we do it in a thread.
    import threading

    def run_scan():
        list(scanner.scan(config))

    t = threading.Thread(target=run_scan)
    t.start()

    time.sleep(0.005)  # Give it time to set _running

    with pytest.raises(RuntimeError):
        list(scanner.scan(config))

    scanner.cancel()
    t.join()
