"""
Scanner CLI command.
"""

import argparse

from sdrmon.cli.monitor import parse_freq
from sdrmon.devices.manager import SDRManager


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", type=int, default=0, help="Device index")
    parser.add_argument(
        "--start", type=str, required=True, help="Start frequency (e.g. 400M)"
    )
    parser.add_argument(
        "--stop", type=str, required=True, help="Stop frequency (e.g. 500M)"
    )
    parser.add_argument("--step", type=str, required=True, help="Step (e.g. 100k)")


def run(args: argparse.Namespace) -> None:
    from rich.console import Console

    console = Console()

    devices = SDRManager.discover()
    if not devices:
        console.print("[red]No SDR devices found.[/red]")
        return

    start_f = parse_freq(args.start)
    stop_f = parse_freq(args.stop)
    step_f = parse_freq(args.step)

    console.print(
        f"Scanning from {start_f} Hz to {stop_f} Hz in steps of {step_f} Hz..."
    )
    console.print(
        "[yellow]Not fully implemented in UI yet, "
        "but CLI scaffolding is present.[/yellow]"
    )
