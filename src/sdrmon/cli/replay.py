"""
Replay CLI command.
"""

import argparse
from pathlib import Path


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", type=str, help="IQ capture file to replay")
    parser.add_argument("--loop", action="store_true", help="Loop the replay")
    parser.add_argument("--rate-control", action="store_true", help="Enforce timing")
    parser.add_argument("--info", action="store_true", help="Print metadata only")


def run(args: argparse.Namespace) -> None:
    from rich.console import Console

    console = Console()

    iq_path = Path(args.file)
    json_path = iq_path.with_suffix(".json")

    if not iq_path.exists():
        console.print(f"[red]File not found: {iq_path}[/red]")
        return

    if not json_path.exists():
        console.print(f"[red]Metadata not found: {json_path}[/red]")
        return

    from sdrmon.capture.metadata import CaptureMetadata

    try:
        meta = CaptureMetadata.load(json_path)
        meta.validate()
    except Exception as e:
        console.print(f"[red]Failed to load metadata: {e}[/red]")
        return

    if args.info:
        console.print("\n[bold]Capture Information[/bold]\n")
        console.print(f"File:             {iq_path.name}")
        console.print(f"Format:           {meta.format} v{meta.version}")
        console.print(f"Sample format:    {meta.sample_format}")
        console.print(f"Center frequency: {meta.center_frequency / 1e6:.3f} MHz")
        console.print(f"Sample rate:      {meta.sample_rate / 1e6:.3f} MS/s")
        console.print(
            f"Duration:         {meta.duration:.2f} s"
            if meta.duration
            else "Duration:         Unknown"
        )
        console.print(f"Samples:          {meta.samples}")
        console.print(f"Backend:          {meta.backend}")
        console.print(f"Device:           {meta.device}")
        console.print(f"Created:          {meta.started_at}")
        return

    from sdrmon.core.device import DeviceInfo
    from sdrmon.replay.replay import ReplayDevice
    from sdrmon.ui.app import start_tui

    dev_info = DeviceInfo(
        driver="replay",
        vendor="SDRmon",
        product=f"Replay: {iq_path.name}",
        serial=str(json_path),
        bus="virtual",
        usb_vid=None,
        usb_pid=None,
    )

    dev = ReplayDevice(dev_info, iq_path, meta)

    # We pass loop and rate_control by monkey patching or we can modify ReplayDevice to take them
    dev.loop = args.loop
    dev.rate_control = args.rate_control

    dev.open()
    try:
        start_tui(dev)
    finally:
        dev.close()
