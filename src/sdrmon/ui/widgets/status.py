"""
Status widget for Textual.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Label

from sdrmon.core.device import SDRDevice


class StatusWidget(Container):
    """Displays device and stream information."""

    frequency: reactive[int] = reactive(0)
    sample_rate: reactive[int] = reactive(0)
    gain: reactive[float] = reactive(0.0)
    fft_size: reactive[int] = reactive(2048)
    window: reactive[str] = reactive("hann")
    noise_floor: reactive[float | None] = reactive(None)
    peak_freq: reactive[float | None] = reactive(None)
    peak_power: reactive[float | None] = reactive(None)

    DEFAULT_CSS = """
    StatusWidget {
        height: 8;
        border: solid $accent;
        padding: 1;
        layout: vertical;
    }
    .status-row {
        height: 1;
        layout: horizontal;
    }
    .status-label {
        width: 15;
        text-style: bold;
    }
    .status-value {
        width: 20;
    }
    """

    def __init__(self, device: SDRDevice | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device

    def compose(self) -> ComposeResult:
        with Horizontal(classes="status-row"):
            yield Label("Frequency:", classes="status-label")
            yield Label("", id="val-freq", classes="status-value")
            yield Label("Sample Rate:", classes="status-label")
            yield Label("", id="val-rate", classes="status-value")

        with Horizontal(classes="status-row"):
            yield Label("Gain:", classes="status-label")
            yield Label("", id="val-gain", classes="status-value")
            yield Label("FFT Size:", classes="status-label")
            yield Label("", id="val-fft", classes="status-value")

        with Horizontal(classes="status-row"):
            yield Label("Window:", classes="status-label")
            yield Label("", id="val-window", classes="status-value")
            yield Label("Noise Floor:", classes="status-label")
            yield Label("", id="val-noise", classes="status-value")

        with Horizontal(classes="status-row"):
            yield Label("Peak:", classes="status-label")
            yield Label("", id="val-peak", classes="status-value")

    def _format_freq(self, hz: float | int | None) -> str:
        if hz is None:
            return "N/A"
        if hz >= 1e9:
            return f"{hz / 1e9:.3f} GHz"
        if hz >= 1e6:
            return f"{hz / 1e6:.3f} MHz"
        if hz >= 1e3:
            return f"{hz / 1e3:.3f} kHz"
        return f"{hz} Hz"

    def watch_frequency(self, value: int) -> None:
        self.query_one("#val-freq", Label).update(self._format_freq(value))

    def watch_sample_rate(self, value: int) -> None:
        if value >= 1e6:
            rate_str = f"{value / 1e6:.3f} MS/s"
        elif value >= 1e3:
            rate_str = f"{value / 1e3:.3f} kS/s"
        else:
            rate_str = f"{value} S/s"
        self.query_one("#val-rate", Label).update(rate_str)

    def watch_gain(self, value: float) -> None:
        if self.device and not self.device.capabilities.gain:
            self.query_one("#val-gain", Label).update("N/A")
        else:
            self.query_one("#val-gain", Label).update(f"{value:.1f} dB")

    def watch_fft_size(self, value: int) -> None:
        self.query_one("#val-fft", Label).update(str(value))

    def watch_window(self, value: str) -> None:
        self.query_one("#val-window", Label).update(value.capitalize())

    def watch_noise_floor(self, value: float | None) -> None:
        if value is None:
            self.query_one("#val-noise", Label).update("N/A")
        else:
            self.query_one("#val-noise", Label).update(f"{value:.1f} dBFS")

    def _update_peak(self) -> None:
        if self.peak_freq is not None and self.peak_power is not None:
            freq_str = self._format_freq(self.peak_freq)
            self.query_one("#val-peak", Label).update(
                f"{freq_str} ({self.peak_power:.1f} dBFS)"
            )
        else:
            self.query_one("#val-peak", Label).update("N/A")

    def watch_peak_freq(self, value: float | None) -> None:
        self._update_peak()

    def watch_peak_power(self, value: float | None) -> None:
        self._update_peak()
