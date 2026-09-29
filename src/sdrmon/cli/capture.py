"""
Capture CLI command.
"""

import argparse
import time
from pathlib import Path

from sdrmon.capture.metadata import CaptureMetadata
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

    dev.set_frequency(freq)
    dev.set_sample_rate(rate)

    out_path = Path(args.output)
    meta_path = out_path.with_suffix(".json")

    meta = CaptureMetadata(
        device=dev_info.product or "Unknown",
        frequency=freq,
        sample_rate=rate,
        gain=None,  # Todo get actual gain
        format="complex64",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        duration=args.duration,
    )

    console.print(f"Starting capture to {out_path} for {args.duration} seconds...")

    stream = dev.start_stream()

    start_t = time.time()

    with open(out_path, "wb") as f:
        try:
            for block in stream:
                f.write(block.samples.tobytes())
                if time.time() - start_t > args.duration:
                    break
        except KeyboardInterrupt:
            console.print("\n[yellow]Capture interrupted.[/yellow]")
            meta.duration = time.time() - start_t

    dev.stop_stream()
    dev.close()

    meta.save(meta_path)
    console.print(f"[green]Capture saved to {out_path} and {meta_path}[/green]")
