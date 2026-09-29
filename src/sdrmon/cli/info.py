"""
Info CLI command.
"""

import argparse

from sdrmon.core.device import DeviceInfo
from sdrmon.devices.manager import SDRManager


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--device", type=int, default=0, help="Device index (default: 0)"
    )


def run(args: argparse.Namespace) -> None:
    from rich.console import Console
    from rich.panel import Panel

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

    caps = dev.capabilities

    info_text = f"[bold]Driver:[/bold] {dev_info.driver}\n"
    info_text += f"[bold]Vendor:[/bold] {dev_info.vendor}\n"
    info_text += f"[bold]Product:[/bold] {dev_info.product}\n"
    info_text += f"[bold]Serial:[/bold] {dev_info.serial}\n"

    caps_text = (
        f"[bold]Frequency tuning:[/bold] "
        f"{'[green]Yes[/green]' if caps.frequency else '[red]No[/red]'}\n"
    )
    caps_text += (
        f"[bold]Sample rate:[/bold] "
        f"{'[green]Yes[/green]' if caps.sample_rate else '[red]No[/red]'}\n"
    )
    caps_text += (
        f"[bold]Gain control:[/bold] "
        f"{'[green]Yes[/green]' if caps.gain else '[red]No[/red]'}\n"
    )
    caps_text += (
        f"[bold]Bandwidth control:[/bold] "
        f"{'[green]Yes[/green]' if caps.bandwidth else '[red]No[/red]'}\n"
    )

    console.print(
        Panel(info_text + "\n" + caps_text, title=f"Device Info: {dev_info.product}")
    )
    dev.close()
