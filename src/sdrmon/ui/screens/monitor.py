"""
Main live monitor screen.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from sdrmon.core.device import SDRDevice
from sdrmon.core.settings import StreamConfig
from sdrmon.ui.components import (
    LIVE_SHORTCUTS,
    AppMode,
    EventLog,
    FrequencyModal,
    GainModal,
    HelpModal,
    SampleRateModal,
    SDRmonFooter,
    SDRmonHeader,
    fmt_freq,
    fmt_rate,
)
from sdrmon.ui.controller import UIController
from sdrmon.ui.widgets.spectrum import SpectrumUpdated, SpectrumWidget
from sdrmon.ui.widgets.waterfall import WaterfallWidget

# ── View mode cycling ─────────────────────────────────────────────────────────


class ViewMode(Enum):
    SPECTRUM = auto()
    WATERFALL = auto()
    BOTH = auto()


_VIEW_LABELS = {
    ViewMode.SPECTRUM: "Spectrum",
    ViewMode.WATERFALL: "Waterfall",
    ViewMode.BOTH: "Spectrum+Waterfall",
}


# ── Monitor Screen ────────────────────────────────────────────────────────────


class MonitorScreen(Screen):
    """
    Full-screen live monitor.

    Layout:
        ┌─ SDRmonHeader ────────────────────────────────┐
        │ StatusBar (1 line)                            │
        │ EventLog (3–4 lines)                          │
        │ SpectrumWidget (1fr)                          │
        │ WaterfallWidget (1fr, optional)               │
        └─ SDRmonFooter ────────────────────────────────┘
    """

    DEFAULT_CSS = """
    MonitorScreen {
        background: #0a0e14;
        layout: vertical;
    }
    #monitor-statusbar {
        height: 1;
        background: #131920;
        padding: 0 1;
        color: #b0bec5;
    }
    #spectrum {
        height: 1fr;
        border: solid #1e3a5c;
        background: #060a10;
    }
    #waterfall {
        height: 1fr;
        border: solid #1e3a5c;
        background: #060a10;
    }
    EventLog {
        height: 4;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("f", "freq", "Frequency"),
        ("g", "gain", "Gain"),
        ("s", "rate", "Sample Rate"),
        ("c", "capture", "Capture"),
        ("S", "scan", "Scanner"),
        ("r", "replay", "Replay"),
        ("d", "device_select", "Device"),
        ("w", "window", "Window"),
        ("v", "toggle_view", "View"),
        ("+", "zoom_in", "Zoom In"),
        ("-", "zoom_out", "Zoom Out"),
        ("?", "help", "Help"),
        ("l", "toggle_loop", "Toggle Loop"),
    ]

    def __init__(self, device: SDRDevice) -> None:
        super().__init__()
        self.device = device
        self.controller: UIController | None = None
        self._view_mode = ViewMode.BOTH
        self._zoom = 1.0
        self._mode = AppMode.LIVE if device.info.driver != "replay" else AppMode.REPLAY

        # Capture state
        self._capture_timer = None
        self._capture_start_time: float = 0.0
        self._capture_duration: float | None = None

    def compose(self) -> ComposeResult:
        hdr = SDRmonHeader(id="monitor-header")
        hdr.mode = self._mode
        yield hdr
        yield Static("", id="monitor-statusbar")
        yield EventLog(id="event-log")
        yield SpectrumWidget(id="spectrum")
        yield WaterfallWidget(id="waterfall")
        ftr = SDRmonFooter(id="monitor-footer")
        ftr.shortcuts = LIVE_SHORTCUTS
        yield ftr

    def on_mount(self) -> None:
        try:
            freq = self.device.get_frequency() or 100_000_000
        except Exception:
            freq = 100_000_000
        try:
            rate = self.device.get_sample_rate() or 2_000_000
        except Exception:
            rate = 2_000_000
        try:
            gain: float | str | None = self.device.get_gain()  # type: ignore[assignment]
        except Exception:
            gain = None

        config = StreamConfig(
            frequency=freq,
            sample_rate=rate,
            gain=gain if isinstance(gain, float) else None,
        )

        self.controller = UIController(self.device, self.app, config)
        self.controller.start()

        # Header
        hdr = self.query_one(SDRmonHeader)
        hdr.device_name = self.device.info.product
        hdr.frequency = freq
        hdr.sample_rate = rate
        if isinstance(gain, (int, float)):
            hdr.gain = gain
        elif isinstance(gain, str):
            hdr.gain = gain

        self._update_statusbar()
        log = self.query_one(EventLog)
        log.log(
            f"Opened {self.device.info.product} — {fmt_freq(freq)} @ {fmt_rate(rate)}",
            "success",
        )

        if self.device.info.driver == "replay":
            self.set_interval(1.0, self._poll_replay_progress)

        self._apply_view()

    def _update_statusbar(self) -> None:
        if not self.controller:
            return
        cfg = self.controller.config
        freq_s = fmt_freq(cfg.frequency)
        rate_s = fmt_rate(cfg.sample_rate)
        zoom_s = f"Zoom {self._zoom:.1f}×"
        view_s = _VIEW_LABELS.get(self._view_mode, "")
        fft_s = f"FFT {self.controller.fft_size}"
        win_s = self.controller.window.capitalize()
        try:
            self.query_one("#monitor-statusbar", Static).update(
                f" {freq_s}  {rate_s}  {fft_s}  {win_s}  {zoom_s}  [{view_s}]"
            )
        except Exception:
            pass

    def _apply_view(self) -> None:
        try:
            spec = self.query_one("#spectrum", SpectrumWidget)
            wf = self.query_one("#waterfall", WaterfallWidget)
            if self._view_mode == ViewMode.SPECTRUM:
                spec.remove_class("hidden")
                wf.add_class("hidden")
            elif self._view_mode == ViewMode.WATERFALL:
                spec.add_class("hidden")
                wf.remove_class("hidden")
            else:  # BOTH
                spec.remove_class("hidden")
                wf.remove_class("hidden")
        except Exception:
            pass

    def _poll_replay_progress(self) -> None:
        if not (self.controller and hasattr(self.controller, "_stream")):
            return
        stream = getattr(self.controller, "_stream", None)
        if stream and hasattr(stream, "position") and hasattr(stream, "meta"):
            pos = getattr(stream, "position", 0)
            meta = getattr(stream, "meta", None)
            if meta:
                total = getattr(meta, "samples", 0)
                if total > 0:
                    pct = (pos / total) * 100
                    try:
                        hdr = self.query_one(SDRmonHeader)
                        hdr.device_name = f"{self.device.info.product}  {pct:.1f}%"
                    except Exception:
                        pass

    def on_spectrum_updated(self, message: SpectrumUpdated) -> None:
        try:
            spec = self.query_one("#spectrum", SpectrumWidget)
            spec.update_result(message.result)
        except Exception:
            pass
        try:
            wf = self.query_one("#waterfall", WaterfallWidget)
            if not wf.has_class("hidden"):
                wf.update_result(message.result)
        except Exception:
            pass
        # Update header
        try:
            hdr = self.query_one(SDRmonHeader)
            hdr.frequency = message.result.center_frequency
            hdr.sample_rate = message.result.sample_rate
        except Exception:
            pass

    def on_stream_error_msg(self, message: Any) -> None:
        log = self.query_one(EventLog)
        log.log(f"Stream error: {message.error}", "error")
        try:
            hdr = self.query_one(SDRmonHeader)
            hdr.is_paused = False
        except Exception:
            pass

    def on_unmount(self) -> None:
        if self.controller:
            self.controller.stop()
        if self._capture_timer:
            self._capture_timer.stop()

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_toggle_pause(self) -> None:
        if not self.controller:
            return
        if self.controller.is_paused():
            self.controller.resume()
            self.query_one(SDRmonHeader).is_paused = False
            self.query_one(EventLog).log("Resumed", "info")
        else:
            self.controller.pause()
            self.query_one(SDRmonHeader).is_paused = True
            self.query_one(EventLog).log("Paused", "warning")

    def action_toggle_view(self) -> None:
        modes = list(ViewMode)
        idx = modes.index(self._view_mode)
        self._view_mode = modes[(idx + 1) % len(modes)]
        self._apply_view()
        self._update_statusbar()
        self.query_one(EventLog).log(f"View: {_VIEW_LABELS[self._view_mode]}", "info")

    def action_zoom_in(self) -> None:
        self._zoom = min(8.0, self._zoom * 2.0)
        spec = self.query_one("#spectrum", SpectrumWidget)
        spec.zoom = self._zoom  # type: ignore[attr-defined]
        self._update_statusbar()

    def action_zoom_out(self) -> None:
        self._zoom = max(0.125, self._zoom / 2.0)
        spec = self.query_one("#spectrum", SpectrumWidget)
        spec.zoom = self._zoom  # type: ignore[attr-defined]
        self._update_statusbar()

    def action_window(self) -> None:
        if not self.controller:
            return
        windows = ["hann", "hamming", "blackman", "rectangular"]
        idx = (
            windows.index(self.controller.window)
            if self.controller.window in windows
            else -1
        )
        nxt = windows[(idx + 1) % len(windows)]
        self.controller.set_window(nxt)
        self.query_one(EventLog).log(f"Window → {nxt.capitalize()}", "info")
        self._update_statusbar()

    def action_freq(self) -> None:
        readonly = self.device.info.driver == "replay"
        freq = self.controller.config.frequency if self.controller else 100_000_000

        def on_result(hz: int | None) -> None:
            if hz is None or not self.controller:
                return
            try:
                self.device.set_frequency(hz)
                self.controller.config = StreamConfig(
                    frequency=hz,
                    sample_rate=self.controller.config.sample_rate,
                    gain=self.controller.config.gain,
                )
                self.query_one(SDRmonHeader).frequency = hz
                self.query_one(EventLog).log(f"Frequency → {fmt_freq(hz)}", "success")
                self._update_statusbar()
            except Exception as e:
                self.query_one(EventLog).log(f"Freq error: {e}", "error")

        self.app.push_screen(FrequencyModal(freq, readonly=readonly), on_result)

    def action_gain(self) -> None:
        caps = self.device.capabilities
        readonly = self.device.info.driver == "replay"
        try:
            current = self.device.get_gain()  # type: ignore[assignment]
        except Exception:
            current = 0.0

        def on_result(value: float | str | None) -> None:
            if value is None or not self.controller:
                return
            try:
                self.device.set_gain(value)  # type: ignore[arg-type]
                self.query_one(SDRmonHeader).gain = value  # type: ignore[assignment]
                self.query_one(EventLog).log(
                    f"Gain → {'AUTO' if value == 'auto' else f'{value} dB'}",
                    "success",
                )
            except Exception as e:
                self.query_one(EventLog).log(f"Gain error: {e}", "error")

        self.app.push_screen(
            GainModal(
                current=current,  # type: ignore[arg-type]
                gain_values=caps.gain_values,
                supported=caps.gain,
                readonly=readonly,
            ),
            on_result,
        )

    def action_rate(self) -> None:
        caps = self.device.capabilities
        readonly = self.device.info.driver == "replay"
        current = self.controller.config.sample_rate if self.controller else 2_000_000

        def on_result(rate: int | None) -> None:
            if rate is None or not self.controller:
                return
            try:
                self.controller.set_sample_rate(rate)
                self.query_one(SDRmonHeader).sample_rate = rate
                self.query_one(EventLog).log(
                    f"Sample Rate → {fmt_rate(rate)}", "success"
                )
                self._update_statusbar()
            except Exception as e:
                self.query_one(EventLog).log(f"Rate error: {e}", "error")

        self.app.push_screen(
            SampleRateModal(current, sample_rates=caps.sample_rates, readonly=readonly),
            on_result,
        )

    def action_help(self) -> None:
        self.app.push_screen(HelpModal())

    def action_device_select(self) -> None:
        """Return to device selection (cleanly stopping stream first)."""
        if self.controller:
            self.controller.stop()
        self.app.switch_to_startup()  # type: ignore[attr-defined]

    def action_scan(self) -> None:
        if not self.controller:
            return
        from sdrmon.scanner.models import ScanConfig
        from sdrmon.ui.screens.scanner import ScannerScreen

        cfg = self.controller.config
        scan_cfg = ScanConfig(
            start_frequency=max(24_000_000, cfg.frequency - cfg.sample_rate),
            stop_frequency=cfg.frequency + cfg.sample_rate,
            step=100_000,
            dwell_time=0.05,
            sample_rate=cfg.sample_rate,
        )
        self.controller.stop()

        def on_dismiss(_: Any) -> None:
            if self.controller:
                self.controller.start()

        self.app.push_screen(ScannerScreen(self.device, scan_cfg), on_dismiss)

    def action_capture(self) -> None:
        if not self.controller:
            return
        if self.controller.recorder:
            # Stop ongoing capture
            self.controller.recorder.close()
            self.controller.recorder = None
            hdr = self.query_one(SDRmonHeader)
            hdr.is_recording = False
            self.query_one(EventLog).log("Capture stopped.", "info")
            if self._capture_timer:
                self._capture_timer.stop()
            return

        import datetime

        from sdrmon.ui.screens.capture import CaptureScreen

        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        freq = self.controller.config.frequency
        default_name = f"capture_{now_str}_{freq}Hz.iq"

        def on_result(result: dict | None) -> None:
            import time

            if not result or not self.controller:
                return
            try:
                from sdrmon.capture.recorder import IQRecorder

                recorder = IQRecorder(result["path"], self.device.info)
                recorder.__enter__()
                self.controller.recorder = recorder
                self._capture_start_time = time.monotonic()
                self._capture_duration = result.get("duration")
                hdr = self.query_one(SDRmonHeader)
                hdr.is_recording = True
                self.query_one(EventLog).log(
                    f"Capture started → {result['path']}", "warning"
                )
                if self._capture_timer:
                    self._capture_timer.stop()
                self._capture_timer = self.set_interval(1.0, self._check_capture)
            except Exception as e:
                self.query_one(EventLog).log(f"Capture error: {e}", "error")

        self.app.push_screen(CaptureScreen(default_path=default_name), on_result)

    def _check_capture(self) -> None:
        import time

        if not self.controller or not self.controller.recorder:
            return
        if self._capture_duration is not None:
            elapsed = time.monotonic() - self._capture_start_time
            if elapsed >= self._capture_duration:
                self.action_capture()
                return
        written = getattr(self.controller.recorder, "_samples_written", 0)
        mb = written * 8 / 1024 / 1024
        path = getattr(self.controller.recorder.iq_path, "name", "?")
        try:
            self.query_one(EventLog).log(f"● Capture {path}: {mb:.1f} MB", "warning")
        except Exception:
            pass

    def action_replay(self) -> None:
        """Open file browser to load replay from within monitor."""
        self.app.open_replay_browser()  # type: ignore[attr-defined]

    def action_toggle_loop(self) -> None:
        if self.device.info.driver != "replay":
            self.query_one(EventLog).log("Not in replay mode.", "warning")
            return
        current_loop = getattr(self.device, "loop", False)
        new_loop = not current_loop
        setattr(self.device, "loop", new_loop)
        if (
            self.controller
            and hasattr(self.controller, "_stream")
            and self.controller._stream
        ):
            stream = self.controller._stream
            if hasattr(stream, "loop"):
                setattr(stream, "loop", new_loop)
        state = "ON" if new_loop else "OFF"
        self.query_one(EventLog).log(f"Loop {state}", "info")
