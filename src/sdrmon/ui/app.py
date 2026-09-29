"""
Textual TUI App.
"""

from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from sdrmon.core.device import SDRDevice


class MonitorScreen(Container):
    """Main monitor screen."""

    def compose(self) -> ComposeResult:
        yield Static("SDRmon Monitor", id="title")
        yield Static("Initializing...", id="status")
        yield Static("Live Spectrum goes here...", id="spectrum")


class SDRmonApp(App[Any]):
    """SDRmon Textual Application."""

    CSS = """
    #title {
        text-align: center;
        background: $primary;
        color: $text;
        text-style: bold;
        padding: 1;
    }
    #status {
        padding: 1;
        border: solid $secondary;
    }
    #spectrum {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "spectrum", "Spectrum"),
        ("w", "waterfall", "Waterfall"),
    ]

    def __init__(self, device: SDRDevice | None = None):
        super().__init__()
        self.device = device

    def compose(self) -> ComposeResult:
        yield Header()
        yield MonitorScreen()
        yield Footer()

    def on_mount(self) -> None:
        if self.device:
            status = self.query_one("#status", Static)
            info = self.device.info
            status.update(f"Device: {info.product} ({info.driver})")


def start_tui(device: SDRDevice | None = None) -> None:
    app = SDRmonApp(device)
    app.run()
