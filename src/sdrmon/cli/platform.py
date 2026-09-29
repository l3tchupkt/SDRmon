"""
Platform CLI command.
"""

import argparse


def setup_parser(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace) -> None:
    from rich.console import Console
    from rich.panel import Panel

    from sdrmon.platform import get_environment_info

    console = Console()
    env = get_environment_info()

    text = f"[bold]OS:[/bold] {env.os}\n"
    text += f"[bold]Architecture:[/bold] {env.architecture}\n"
    text += f"[bold]Python:[/bold] {env.python_version.split()[0]}\n"
    text += f"[bold]NumPy:[/bold] {env.numpy_version}\n"
    text += f"[bold]SDRmon:[/bold] {env.sdrmon_version}\n"
    text += f"[bold]Available Backends:[/bold] {', '.join(env.available_backends) if env.available_backends else 'None'}\n"

    console.print(Panel(text, title="Platform Environment"))
