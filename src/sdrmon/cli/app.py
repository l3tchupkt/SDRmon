"""
Main CLI application for SDRmon.
"""

import argparse
import logging
import sys

from sdrmon import __version__
from sdrmon.backends import initialize_backends
from sdrmon.cli import devices, info


def main():
    initialize_backends()
    parser = argparse.ArgumentParser(description="SDRmon - Terminal-first SDR toolkit")
    parser.add_argument("--version", action="version", version=f"SDRmon {__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Devices command
    devices_parser = subparsers.add_parser("devices", help="List connected SDR devices")
    devices.setup_parser(devices_parser)

    # Info command
    info_parser = subparsers.add_parser(
        "info", help="Show information about a specific device"
    )
    info.setup_parser(info_parser)

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start the main TUI monitor")
    from sdrmon.cli import monitor

    monitor.setup_parser(monitor_parser)

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture IQ to a file")
    from sdrmon.cli import capture

    capture.setup_parser(capture_parser)

    # Other placeholders
    # spectrum_parser = subparsers.add_parser("spectrum", help="Start the spectrum TUI")
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan a frequency range")
    from sdrmon.cli import scan

    scan.setup_parser(scan_parser)

    # replay_parser = subparsers.add_parser("replay", help="Replay a captured IQ file")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if getattr(args, "command", None) == "devices":
        devices.run(args)
    elif getattr(args, "command", None) == "info":
        info.run(args)
    elif getattr(args, "command", None) == "monitor":
        monitor.run(args)
    elif getattr(args, "command", None) == "capture":
        capture.run(args)
    elif getattr(args, "command", None) == "scan":
        scan.run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
