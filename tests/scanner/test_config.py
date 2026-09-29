import pytest

from sdrmon.scanner import ScanConfig


def test_scan_config_valid():
    config = ScanConfig(
        start_frequency=100_000_000,
        stop_frequency=110_000_000,
        step=250_000,
        dwell_time=0.1,
        sample_rate=2_000_000,
    )
    assert config.start_frequency == 100_000_000


def test_scan_config_invalid_frequencies():
    with pytest.raises(ValueError):
        ScanConfig(
            start_frequency=110_000_000,
            stop_frequency=100_000_000,  # stop < start
            step=250_000,
            dwell_time=0.1,
            sample_rate=2_000_000,
        )


def test_scan_config_invalid_step():
    with pytest.raises(ValueError):
        ScanConfig(
            start_frequency=100_000_000,
            stop_frequency=110_000_000,
            step=0,
            dwell_time=0.1,
            sample_rate=2_000_000,
        )
