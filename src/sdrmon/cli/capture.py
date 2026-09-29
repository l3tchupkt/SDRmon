"""
Capture CLI command.
"""

import argparse
import time
from pathlib import Path

from sdrmon.cli.monitor import parse_freq
from sdrmon.core.device import DeviceInfo
from sdrmon.devices.manager import SDRManager


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", type=int, default=0, help="Device index")
    parser.add_argument(
        "--frequency", type=str, required=True, help="Center frequency (e.g. 100M)"
    )
    parser.add_argument(
        "--sample-rate", type=str, required=True, help="Sample rate (e.g. 2.4M)"
    )
    parser.add_argument(
        "--duration", type=float, required=True, help="Duration in seconds"
    )
    parser.add_argument("--output", type=str, required=True, help="Output IQ file path")


def run(args: argparse.Namespace) -> None:
    from rich.console import Console

    console = Console()

    devices = SDRManager.discover()

    if not devices:
        console.print("[red]No SDR devices found.[/red]")
        return

    dev_info: DeviceInfo = devices[args.device]
    try:
        dev = SDRManager.open(dev_info)
    except Exception as e:
        console.print(f"[red]Failed to open device: {e}[/red]")
        return

    freq = parse_freq(args.frequency)
    rate = parse_freq(args.sample_rate)

    if freq is None or rate is None:
        console.print("[red]Invalid frequency or sample rate format.[/red]")
        return

    from sdrmon.capture.recorder import IQRecorder
    from sdrmon.core.settings import StreamConfig

    config = StreamConfig(
        frequency=freq,
        sample_rate=rate,
    )

    console.print(f"Starting capture to {args.output} for {args.duration} seconds...")

    stream = dev.stream(config)

    start_t = time.time()

    out_path = Path(args.output)
    meta_path = out_path.with_suffix(".json")

    with stream:
        with IQRecorder(out_path, device_info=dev_info) as recorder:
            try:
                for block in stream:
                    recorder.write(block)
                    if time.time() - start_t > args.duration:
                        break
            except KeyboardInterrupt:
                console.print("\n[yellow]Capture interrupted.[/yellow]")

    dev.close()

    console.print(f"[green]Capture saved to {out_path} and {meta_path}[/green]")
