"""
CLI tests.
"""

import argparse
from sdrmon.cli.info import run as run_info
from sdrmon.cli.capture import run as run_capture
from sdrmon.cli.monitor import parse_freq


def test_parse_freq():
    assert parse_freq("100") == 100
    assert parse_freq("1k") == 1000
    assert parse_freq("2.5m") == 2_500_000
    assert parse_freq("1G") == 1_000_000_000


def test_cli_info():
    # Should run without crashing, using rich to print
    args = argparse.Namespace(device=0)
    # This might print "No SDR devices found" or similar
    # It should not throw.
    run_info(args)


def test_cli_platform():
    from sdrmon.cli.platform import run as run_platform

    args = argparse.Namespace()
    run_platform(args)
