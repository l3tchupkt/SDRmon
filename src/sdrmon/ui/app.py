"""
Textual TUI App.
"""

from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header

from sdrmon.core.device import SDRDevice
from sdrmon.core.settings import StreamConfig
from sdrmon.ui.controller import UIController
from sdrmon.ui.widgets.spectrum import SpectrumUpdated, SpectrumWidget
from sdrmon.ui.widgets.status import StatusWidget


class MonitorScreen(Container):
    """Main monitor screen."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield StatusWidget(id="status-panel")
            yield SpectrumWidget(id="spectrum")


class SDRmonApp(App[Any]):
    """SDRmon Textual Application."""

    CSS = """
    #status-panel {
        height: 6;
        border: solid $accent;
    }
    #spectrum {
        height: 1fr;
        border: solid $primary;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("f", "freq", "Frequency"),
        ("g", "gain", "Gain"),
        ("s", "rate", "Sample Rate"),
        ("w", "window", "Window"),
        ("+", "zoom_in", "Zoom In"),
        ("-", "zoom_out", "Zoom Out"),
        ("?", "help", "Help"),
    ]

    def __init__(self, device: SDRDevice | None = None):
        super().__init__()
        self.device = device
        self.controller: UIController | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield MonitorScreen()
        yield Footer()

    def on_mount(self) -> None:
        if self.device:
            self.title = f"SDRmon - {self.device.info.product}"

            # Start streaming
            config = StreamConfig(
                frequency=self.device.get_frequency() or 100_000_000,
                sample_rate=self.device.get_sample_rate() or 2_000_000,
                gain=self.device.get_gain(),
            )

            self.controller = UIController(self.device, self, config)
            self.controller.start()

            status = self.query_one(StatusWidget)
            status.device = self.device
            status.frequency = config.frequency
            status.sample_rate = config.sample_rate
            if config.gain is not None:
                status.gain = config.gain
            status.fft_size = self.controller.fft_size
            status.window = self.controller.window

    def on_unmount(self) -> None:
        if self.controller:
            self.controller.stop()

    def on_spectrum_updated(self, message: SpectrumUpdated) -> None:
        spectrum = self.query_one(SpectrumWidget)
        status = self.query_one(StatusWidget)

        spectrum.update_result(message.result)

        status.noise_floor = message.result.noise_floor
        status.peak_freq = message.result.peak_frequency
        status.peak_power = message.result.peak_power
        # Update current values in case they changed outside
        status.frequency = message.result.center_frequency
        status.sample_rate = message.result.sample_rate

    def action_toggle_pause(self) -> None:
        if self.controller:
            if self.controller.is_paused():
                self.controller.resume()
                self.sub_title = ""
            else:
                self.controller.pause()
                self.sub_title = "[PAUSED]"

    def action_freq(self) -> None:
        self.notify(
            "Frequency tuning modal not yet implemented in Phase 5.",
            severity="information",
        )

    def action_gain(self) -> None:
        self.notify(
            "Gain adjustment modal not yet implemented in Phase 5.",
            severity="information",
        )

    def action_rate(self) -> None:
        self.notify(
            "Sample rate selection modal not yet implemented in Phase 5.",
            severity="information",
        )

    def action_window(self) -> None:
        # Cycle window
        if self.controller:
            windows = ["hann", "hamming", "blackman", "rectangular"]
            idx = (
                windows.index(self.controller.window)
                if self.controller.window in windows
                else -1
            )
            next_window = windows[(idx + 1) % len(windows)]
            self.controller.set_window(next_window)
            status = self.query_one(StatusWidget)
            status.window = next_window
            self.notify(f"Window changed to {next_window}", severity="information")

    def action_zoom_in(self) -> None:
        self.notify("Zoom not yet implemented in Phase 5.", severity="information")

    def action_zoom_out(self) -> None:
        self.notify("Zoom not yet implemented in Phase 5.", severity="information")

    def action_help(self) -> None:
        self.notify(
            "Help modal not yet implemented in Phase 5.", severity="information"
        )


def start_tui(device: SDRDevice | None = None) -> None:
    app = SDRmonApp(device)
    app.run()
