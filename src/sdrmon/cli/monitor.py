"""
Monitor CLI command.
"""

import argparse

from sdrmon.core.device import DeviceInfo
from sdrmon.devices.manager import SDRManager


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", type=int, default=0, help="Device index")
    parser.add_argument("--frequency", type=str, help="Center frequency (e.g. 100M)")
    parser.add_argument("--sample-rate", type=str, help="Sample rate (e.g. 2.4M)")


def parse_freq(val: str | None) -> int | None:
    if not val:
        return None
    val = val.lower()
    mult = 1
    if val.endswith("k"):
        mult = 1_000
        val = val[:-1]
    elif val.endswith("m"):
        mult = 1_000_000
        val = val[:-1]
    elif val.endswith("g"):
        mult = 1_000_000_000
        val = val[:-1]
    return int(float(val) * mult)


def run(args: argparse.Namespace) -> None:
    from rich.console import Console

    console = Console()

    devices = SDRManager.discover()

    if not devices:
        console.print("[red]No SDR devices found.[/red]")
        return

    if args.device < 0 or args.device >= len(devices):
        console.print(f"[red]Invalid device index {args.device}.[/red]")
        return

    dev_info: DeviceInfo = devices[args.device]

    try:
        dev = SDRManager.open(dev_info)
    except Exception as e:
        console.print(f"[red]Failed to open device: {e}[/red]")
        return

    freq = parse_freq(args.frequency)
    if freq:
        dev.set_frequency(freq)

    rate = parse_freq(args.sample_rate)
    if rate:
        dev.set_sample_rate(rate)

    from sdrmon.ui.app import start_tui

    start_tui(dev)
