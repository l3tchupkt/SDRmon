"""
Devices CLI command.
"""

import argparse

from sdrmon.devices.manager import SDRManager


def setup_parser(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace) -> None:
    from rich.console import Console
    from rich.table import Table

    console = Console()
    devices = SDRManager.discover()

    if not devices:
        console.print("[red]No SDR devices found.[/red]")
        return

    table = Table(title="Connected SDR Devices")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Device ID", style="blue")
    table.add_column("Driver", style="magenta")
    table.add_column("Vendor", style="green")
    table.add_column("Product", style="green")
    table.add_column("Serial", style="yellow")

    for i, dev in enumerate(devices):
        table.add_row(
            str(i),
            dev.device_id,
            dev.driver,
            dev.vendor,
            dev.product,
            dev.serial or "N/A",
        )

    console.print(table)
