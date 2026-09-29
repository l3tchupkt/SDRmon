"""
Scan CLI command.
"""

import argparse
import csv
import json
import sys
import time
from typing import TextIO

from sdrmon.core.device import DeviceInfo
from sdrmon.devices.manager import SDRManager
from sdrmon.scanner import ScanConfig, Scanner


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", type=int, default=0, help="Device index")
    parser.add_argument("--fake", action="store_true", help="Use FakeSDR backend")
    parser.add_argument(
        "--start", type=str, required=True, help="Start frequency (e.g. 100M)"
    )
    parser.add_argument(
        "--stop", type=str, required=True, help="Stop frequency (e.g. 110M)"
    )
    parser.add_argument("--step", type=str, required=True, help="Step size (e.g. 250k)")
    parser.add_argument(
        "--dwell", type=float, default=0.1, help="Dwell time in seconds (e.g. 0.1)"
    )
    parser.add_argument(
        "--sample-rate", type=str, default="2M", help="Sample rate (e.g. 2M)"
    )
    parser.add_argument("--fft-size", type=int, default=2048, help="FFT size")
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Occupancy threshold (dB above noise floor)",
    )
    parser.add_argument(
        "--averaging", type=int, default=1, help="Number of measurements to average"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument("--csv", type=str, help="Output results to CSV file")


def parse_freq(val: str) -> int:
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

    if args.fake:
        from sdrmon.backends.generic.fake import FakeSDRDevice

        dev_info = DeviceInfo(
            driver="fake",
            product="FakeSDR",
            vendor="Virtual",
            serial="1",
            bus=None,
            usb_pid=None,
            usb_vid=None,
        )
        dev = FakeSDRDevice(dev_info, seed=42)
        dev.open()
    else:
        devices = SDRManager.discover()
        if not devices:
            console.print("[red]No SDR devices found.[/red]")
            sys.exit(1)

        if args.device < 0 or args.device >= len(devices):
            console.print(f"[red]Invalid device index {args.device}.[/red]")
            sys.exit(1)

        dev_info: DeviceInfo = devices[args.device]

        try:
            dev = SDRManager.open(dev_info)
        except Exception as e:
            console.print(f"[red]Failed to open device: {e}[/red]")
            sys.exit(1)

    try:
        config = ScanConfig(
            start_frequency=parse_freq(args.start),
            stop_frequency=parse_freq(args.stop),
            step=parse_freq(args.step),
            dwell_time=args.dwell,
            sample_rate=parse_freq(args.sample_rate),
            fft_size=args.fft_size,
            threshold=args.threshold,
            averaging=args.averaging,
        )
    except Exception as e:
        console.print(f"[red]Invalid scan configuration: {e}[/red]")
        sys.exit(1)

    scanner = Scanner(dev)
    results = []

    csv_file: TextIO | None = None
    csv_writer = None

    if args.csv:
        csv_file = open(args.csv, "w", newline="", encoding="utf-8")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            [
                "frequency",
                "peak_frequency",
                "peak_power",
                "noise_floor",
                "occupied",
                "timestamp",
            ]
        )

    if not args.json:
        console.print("\n[bold]SDRmon Scanner[/bold]\n")
        console.print(
            f"Range       {config.start_frequency / 1e6:.3f} → {config.stop_frequency / 1e6:.3f} MHz"
        )
        console.print(f"Step        {config.step / 1e3:.3f} kHz")
        console.print(f"Dwell       {config.dwell_time * 1000:.0f} ms")
        console.print(f"Sample Rate {config.sample_rate / 1e6:.3f} MS/s\n")
        console.print("Scanning...\n")

    started_at = time.time()
    try:
        for res in scanner.scan(config):
            results.append(res)

            if csv_writer:
                csv_writer.writerow(
                    [
                        res.frequency,
                        res.peak_frequency,
                        res.peak_power,
                        res.noise_floor,
                        res.occupied,
                        res.timestamp,
                    ]
                )

            if args.json:
                data = {
                    "frequency": res.frequency,
                    "peak_frequency": res.peak_frequency,
                    "peak_power": res.peak_power,
                    "noise_floor": res.noise_floor,
                    "occupied": res.occupied,
                    "timestamp": res.timestamp,
                }
                print(json.dumps(data))
            else:
                status = "[red]ACTIVE[/red]" if res.occupied else "idle"
                console.print(
                    f"{res.frequency / 1e6:10.3f} MHz   {res.peak_power:6.1f} dBFS   {status}"
                )

    except KeyboardInterrupt:
        scanner.cancel()
        if not args.json:
            console.print("\n[yellow]Scan cancelled.[/yellow]")

    completed_at = time.time()

    if csv_file:
        csv_file.close()

    if not args.json:
        occupied = sum(1 for r in results if r.occupied)
        console.print(f"\nCompleted: {len(results)} steps")
        console.print(f"Active:    {occupied}")
        console.print(f"Duration:  {completed_at - started_at:.2f} s")
