"""
Textual TUI App.
"""

from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.timer import Timer
from textual.widgets import Footer, Header

from sdrmon.core.device import SDRDevice
from sdrmon.core.settings import StreamConfig
from sdrmon.scanner.models import ScanConfig
from sdrmon.ui.controller import UIController
from sdrmon.ui.screens.scanner import ScannerScreen
from sdrmon.ui.widgets.spectrum import SpectrumUpdated, SpectrumWidget
from sdrmon.ui.widgets.status import StatusWidget
from sdrmon.ui.widgets.waterfall import WaterfallWidget


class MonitorScreen(Container):
    """Main monitor screen."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield StatusWidget(id="status-panel")
            yield SpectrumWidget(id="spectrum")
            yield WaterfallWidget(id="waterfall", classes="hidden")


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
    #waterfall {
        height: 1fr;
        border: solid $secondary;
    }
    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("f", "freq", "Frequency"),
        ("g", "gain", "Gain"),
        ("s", "rate", "Sample Rate"),
        ("c", "toggle_capture", "Capture"),
        ("S", "scan", "Scanner"),
        ("w", "window", "Window"),
        ("v", "toggle_waterfall", "Waterfall"),
        ("+", "zoom_in", "Zoom In"),
        ("-", "zoom_out", "Zoom Out"),
        ("?", "help", "Help"),
        ("r", "restart_replay", "Restart Replay"),
        ("l", "toggle_loop", "Toggle Loop"),
    ]

    def __init__(self, device: SDRDevice | None = None):
        super().__init__()
        self.device = device
        self.controller: UIController | None = None
        self._capture_timer: Timer | None = None
        self._capture_start_time: float = 0.0
        self._capture_duration: float | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield MonitorScreen()
        yield Footer()

    def on_mount(self) -> None:
        if self.device:
            if self.device.info.driver == "replay":
                self.title = f"REPLAY - {self.device.info.product}"
            else:
                self.title = f"LIVE - {self.device.info.product}"

            # Start streaming
            config = StreamConfig(
                frequency=self.device.get_frequency() or 100_000_000,
                sample_rate=self.device.get_sample_rate() or 2_000_000,
                gain=self.device.get_gain(),
            )

            self.controller = UIController(self.device, self, config)
            self.controller.start()
            
            if self.device.info.driver == "replay":
                self.set_interval(1.0, self._update_replay_progress)

            status = self.query_one(StatusWidget)
            status.device = self.device
            status.frequency = config.frequency
            status.sample_rate = config.sample_rate
            if config.gain is not None:
                status.gain = config.gain
            status.fft_size = self.controller.fft_size
            status.window = self.controller.window

    def _update_replay_progress(self) -> None:
        if self.device and self.device.info.driver == "replay" and self.controller and hasattr(self.controller, "_stream"):
            stream = getattr(self.controller, "_stream", None)
            if stream and hasattr(stream, "position") and hasattr(stream, "meta"):
                pos = getattr(stream, "position", 0)
                meta = getattr(stream, "meta", None)
                if meta:
                    samples = getattr(meta, "samples", 0)
                    if samples > 0:
                        pct = (pos / samples) * 100
                        self.sub_title = f"[REPLAY] {pct:.1f}% ({pos}/{samples})"
                    else:
                        self.sub_title = f"[REPLAY] {pos} samples"

    def on_unmount(self) -> None:
        if self.controller:
            self.controller.stop()

    def on_spectrum_updated(self, message: SpectrumUpdated) -> None:
        spectrum = self.query_one(SpectrumWidget)
        status = self.query_one(StatusWidget)
        waterfall = self.query_one(WaterfallWidget)

        spectrum.update_result(message.result)
        if not waterfall.has_class("hidden"):
            waterfall.update_result(message.result)

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

    def action_toggle_waterfall(self) -> None:
        waterfall = self.query_one(WaterfallWidget)
        if waterfall.has_class("hidden"):
            waterfall.remove_class("hidden")
        else:
            waterfall.add_class("hidden")

    def on_stream_error_msg(self, message) -> None:
        self.notify(f"STREAM ERROR: {message.error}", severity="error")
        self.sub_title = "[ERROR]"

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

    def action_scan(self) -> None:
        if not self.device or not self.controller:
            return

        # Pause background spectrum acquisition and stop stream so scanner can use it
        self.controller.stop()

        # Simple default scan around current frequency
        freq = self.controller.config.frequency
        rate = self.controller.config.sample_rate

        config = ScanConfig(
            start_frequency=freq - rate,
            stop_frequency=freq + rate,
            step=100_000,
            dwell_time=0.1,
            sample_rate=rate,
        )

        def on_scanner_dismiss():
            # Resume background controller
            if self.controller:
                self.controller.start()

        self.push_screen(
            ScannerScreen(self.device, config), callback=lambda _: on_scanner_dismiss()
        )

    def action_toggle_capture(self) -> None:
        if not self.device or not self.controller:
            return

        # If already recording, stop
        if self.controller.recorder:
            self.controller.recorder.close()
            self.controller.recorder = None
            self.sub_title = ""
            self.notify("Capture stopped.", severity="information")
            # stop update timer
            if self._capture_timer:
                self._capture_timer.stop()
            return

        # Otherwise, open dialog
        import time

        from sdrmon.ui.screens.capture import CaptureScreen

        def start_capture(result):
            if not result or not self.device or not self.controller:
                return

            try:
                from sdrmon.capture.recorder import IQRecorder

                recorder = IQRecorder(result["path"], self.device.info)
                recorder.__enter__()  # Open file
                self.controller.recorder = recorder

                # store capture state for timer
                self._capture_start_time = time.monotonic()
                self._capture_duration = result["duration"]

                self.sub_title = f"[RECORDING to {result['path']}]"

                # Start a timer to update status or auto-stop
                if self._capture_timer:
                    self._capture_timer.stop()
                self._capture_timer = self.set_interval(1.0, self._check_capture)

            except Exception as e:
                self.notify(f"Failed to start capture: {e}", severity="error")

        # Generate default filename
        import datetime

        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        freq = self.controller.config.frequency
        default_name = f"capture_{now_str}_{freq}Hz.iq"

        self.push_screen(
            CaptureScreen(default_path=default_name), callback=start_capture
        )

    def _check_capture(self) -> None:
        if not self.controller or not self.controller.recorder:
            return

        import time

        # Auto-stop if duration specified
        if self._capture_duration is not None:
            elapsed = time.monotonic() - self._capture_start_time
            if elapsed >= self._capture_duration:
                self.action_toggle_capture()
                return

        # Update status
        written = self.controller.recorder._samples_written
        mbytes = written * 8 / 1024 / 1024

        # update title
        path = self.controller.recorder.iq_path.name
        self.sub_title = f"[RECORDING] {path} ({mbytes:.1f} MB)"

    def on_capture_error_msg(self, message) -> None:
        from sdrmon.ui.screens.capture import CaptureErrorMsg

        if isinstance(message, CaptureErrorMsg):
            self.notify(f"Capture error: {message.error}", severity="error")
            if self.controller and self.controller.recorder:
                self.controller.recorder.close()
                self.controller.recorder = None
            self.sub_title = "[CAPTURE ERROR]"
            if self._capture_timer:
                self._capture_timer.stop()

    def action_restart_replay(self) -> None:
        if self.device and self.device.info.driver == "replay" and self.controller:
            self.controller.stop()
            # The device keeps track of the file via the ReplayStream.
            # We just need to stop the controller and start it again.
            # ReplayStream will re-open the file if closed, but actually ReplayDevice creates a new ReplayStream.
            self.controller.start()

            # Reset widgets
            spectrum = self.query_one(SpectrumWidget)
            waterfall = self.query_one(WaterfallWidget)
            waterfall._buffer = None
            self.notify("Replay restarted.")
        else:
            self.notify("Not in replay mode.", severity="warning")

    def action_toggle_loop(self) -> None:
        if self.device and self.device.info.driver == "replay":
            current_loop = getattr(self.device, "loop", False)
            new_loop = not current_loop
            setattr(self.device, "loop", new_loop)

            if self.controller and hasattr(self.controller._stream, "loop"):
                setattr(self.controller._stream, "loop", new_loop)

            state = "ON" if new_loop else "OFF"
            self.notify(f"Replay loop {state}")
        else:
            self.notify("Not in replay mode.", severity="warning")


def start_tui(device: SDRDevice | None = None) -> None:
    app = SDRmonApp(device)
    app.run()
