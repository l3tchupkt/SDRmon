"""
Main CLI application for SDRmon.

When called with no subcommand, launches the full interactive TUI.
"""

import argparse
import logging
import sys

from sdrmon import __version__
from sdrmon.backends import initialize_backends


def main() -> None:
    initialize_backends()
    parser = argparse.ArgumentParser(
        description="SDRmon — Terminal-first SDR monitor",
        epilog="Run without arguments to launch the interactive application.",
    )
    parser.add_argument("--version", action="version", version=f"SDRmon {__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Devices command
    devices_parser = subparsers.add_parser("devices", help="List connected SDR devices")
    from sdrmon.cli import devices as _devices_mod

    _devices_mod.setup_parser(devices_parser)

    # Info command
    info_parser = subparsers.add_parser(
        "info", help="Show information about a specific device"
    )
    from sdrmon.cli import info as _info_mod

    _info_mod.setup_parser(info_parser)

    # Monitor command (explicit TUI, preserves backwards compat)
    monitor_parser = subparsers.add_parser(
        "monitor", help="Start the main TUI monitor (equivalent to sdrmon with no args)"
    )
    from sdrmon.cli import monitor as _monitor_mod

    _monitor_mod.setup_parser(monitor_parser)

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture IQ to a file")
    from sdrmon.cli import capture as _capture_mod

    _capture_mod.setup_parser(capture_parser)

    # Doctor command
    doctor_parser = subparsers.add_parser(
        "doctor", help="Show environment diagnostics"
    )
    from sdrmon.cli import doctor as _doctor_mod

    _doctor_mod.setup_parser(doctor_parser)

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan a frequency range")
    from sdrmon.cli import scan as _scan_mod

    _scan_mod.setup_parser(scan_parser)

    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a captured IQ file")
    from sdrmon.cli import replay as _replay_mod

    _replay_mod.setup_parser(replay_parser)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    cmd = getattr(args, "command", None)

    if cmd is None:
        # ── Default: launch the interactive terminal application ──────────
        from sdrmon.ui.app import start_tui

        start_tui()

    elif cmd == "devices":
        _devices_mod.run(args)
    elif cmd == "info":
        _info_mod.run(args)
    elif cmd == "monitor":
        _monitor_mod.run(args)
    elif cmd == "capture":
        _capture_mod.run(args)
    elif cmd == "scan":
        _scan_mod.run(args)
    elif cmd == "doctor":
        _doctor_mod.run(args)
    elif cmd == "replay":
        _replay_mod.run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
