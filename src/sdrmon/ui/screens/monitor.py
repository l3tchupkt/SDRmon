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
    AppMode,
    EventLog,
    HelpModal,
    SDRmonHeader,
    fmt_freq,
    fmt_rate,
)
from sdrmon.ui.controller import UIController
from sdrmon.ui.widgets.controls import AudioSettingsChanged
from sdrmon.ui.widgets.spectrum import (
    SpectrumClick,
    SpectrumUpdated,
    SpectrumWidget,
    ZoomMessage,
)
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
    #monitor-body {
        layout: horizontal;
        height: 1fr;
    }
    #vis-container {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }
    #spectrum {
        height: 1fr;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        border-title-style: bold;
        background: #060a10;
    }
    #waterfall {
        height: 1fr;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        border-title-style: bold;
        background: #060a10;
    }
    #control-sidebar {
        width: 48;
        height: 100%;
        border-left: solid #1e3a5c;
        background: #060a10;
        layout: vertical;
    }
    #sidebar-scroll {
        width: 100%;
        height: 1fr;
        layout: vertical;
    }
    #event-log {
        height: 1fr;
        min-height: 5;
        border: solid #1e3a5c;
        border-title-color: #00b0ff;
        background: #131920;
    }

    #monitor-body.narrow {
        layout: vertical;
    }
    #monitor-body.narrow > #control-sidebar {
        width: 100%;
        height: auto;
        max-height: 20;
        border-left: none;
        border-top: solid #1e3a5c;
    }
    #monitor-body.narrow #sidebar-scroll {
        height: auto;
    }
    #monitor-body.narrow #event-log {
        height: 6;
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
        ("]", "scale_up", "Scale Up"),
        ("[", "scale_down", "Scale Down"),
        ("a", "auto_scale", "Auto Scale"),
        ("?", "help", "Help"),
        ("l", "toggle_loop", "Toggle Loop"),
    ]

    def __init__(self, device: SDRDevice) -> None:
        super().__init__()
        self.device = device
        self.controller: UIController | None = None
        self._view_mode = ViewMode.BOTH
        self._spectrum_zoom = 1.0
        self._waterfall_zoom = 1.0
        self._mode = (
            AppMode.STARTING if device.info.driver != "replay" else AppMode.REPLAY
        )

        # Capture state
        self._capture_timer = None
        self._capture_start_time: float = 0.0
        self._capture_duration: float | None = None

    def compose(self) -> ComposeResult:
        hdr = SDRmonHeader(id="monitor-header")
        hdr.mode = self._mode
        yield hdr

        from textual.containers import Horizontal, Vertical, VerticalScroll

        from sdrmon.ui.widgets.controls import (
            ActionButtons,
            AudioControl,
            DeviceControl,
            FrequencyControl,
            GainControl,
            RateControl,
            ZoomScaleControl,
        )

        with Horizontal(id="monitor-body"):
            with Vertical(id="vis-container"):
                yield SpectrumWidget(id="spectrum")
                yield WaterfallWidget(id="waterfall")

            with Vertical(id="control-sidebar"):
                with VerticalScroll(id="sidebar-scroll"):
                    yield FrequencyControl(id="ctrl-freq")
                    yield GainControl(id="ctrl-gain")
                    yield RateControl(id="ctrl-rate")
                    yield ZoomScaleControl(id="ctrl-zoom")
                    yield AudioControl(id="ctrl-audio")
                    yield DeviceControl(id="ctrl-device")
                    yield EventLog(id="event-log")
                yield ActionButtons(id="ctrl-actions")

    def on_resize(self, event: Any) -> None:
        try:
            body = self.query_one("#monitor-body")
            if event.size.width < 110:
                body.add_class("narrow")
            else:
                body.remove_class("narrow")
        except Exception:
            pass

    def on_mount(self) -> None:
        self.query_one("#spectrum", SpectrumWidget).border_title = "SPECTRUM"
        self.query_one("#waterfall", WaterfallWidget).border_title = "WATERFALL"
        self.query_one("#event-log", EventLog).border_title = "EVENTS"

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

        self.controller = UIController(self.device, self, config)
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

        # Init Controls
        try:
            from sdrmon.ui.widgets.controls import FrequencyControl, GainControl

            self.query_one("#ctrl-freq", FrequencyControl).frequency = freq
            if isinstance(gain, (int, float)):
                self.query_one("#ctrl-gain", GainControl).gain = gain
        except Exception:
            pass

        self._update_device_info()
        log = self.query_one(EventLog)
        log.log(
            f"Opened {self.device.info.product} — {fmt_freq(freq)} @ {fmt_rate(rate)}",
            "success",
        )

        if self.device.info.driver == "replay":
            self.set_interval(1.0, self._poll_replay_progress)

        self._apply_view()

    def _update_device_info(self, peak: float | None = None) -> None:
        if not self.controller:
            return
        cfg = self.controller.config
        info = self.device.info

        freq_s = fmt_freq(cfg.frequency)
        span_s = fmt_rate(cfg.sample_rate).replace("S/s", "Hz")
        peak_s = f"{peak:.1f} dBFS" if peak is not None else "--"

        status_s = "[#00e676]● LIVE[/]"
        if self._mode == AppMode.REPLAY:
            status_s = "[#00b0ff]► REPLAY[/]"
        elif self._mode == AppMode.STARTING:
            status_s = "[#ffff00]● STARTING[/]"

        try:
            self.query_one("#dev-name", Static).update(info.product)
            self.query_one("#dev-status", Static).update(status_s)
            self.query_one("#dev-rate", Static).update(span_s)
            self.query_one("#dev-peak", Static).update(peak_s)

            # Update Zoom/Scale labels
            self.query_one("#sz-val", Static).update(f"{self._spectrum_zoom:.1f}x")
            self.query_one("#wz-val", Static).update(f"{self._waterfall_zoom:.1f}x")
            spec = self.query_one("#spectrum", SpectrumWidget)
            sc_val = (
                "AUTO" if spec.auto_scale_enabled else f"{spec.manual_range:.0f} dB"
            )
            self.query_one("#sc-val", Static).update(sc_val)
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
        # Update header and info
        try:
            # Transition to LIVE state once actual data is received
            hdr = self.query_one(SDRmonHeader)
            if self._mode == AppMode.STARTING:
                self._mode = AppMode.LIVE
                hdr.mode = AppMode.LIVE

            hdr.frequency = message.result.center_frequency
            hdr.sample_rate = message.result.sample_rate
            peak = message.result.peak_power
            self._update_device_info(peak=float(peak) if peak is not None else None)
        except Exception:
            pass

    def on_zoom_message(self, message: ZoomMessage) -> None:
        if message.target == "spectrum":
            if message.direction == "in":
                self._spectrum_zoom = min(32.0, self._spectrum_zoom * 2.0)
            else:
                self._spectrum_zoom = max(1.0, self._spectrum_zoom / 2.0)
            spec = self.query_one("#spectrum", SpectrumWidget)
            spec.zoom = self._spectrum_zoom  # type: ignore[attr-defined]
        else:
            if message.direction == "in":
                self._waterfall_zoom = min(32.0, self._waterfall_zoom * 2.0)
            else:
                self._waterfall_zoom = max(1.0, self._waterfall_zoom / 2.0)
            wf = self.query_one("#waterfall", WaterfallWidget)
            wf.zoom = self._waterfall_zoom  # type: ignore[attr-defined]
        self._update_device_info()

    def on_gain_changed(self, message: Any) -> None:
        if not self.controller or self.device.info.driver == "replay":
            return
        try:
            self.device.set_gain(message.gain)
            self.controller.config = StreamConfig(
                frequency=self.controller.config.frequency,
                sample_rate=self.controller.config.sample_rate,
                gain=message.gain,
            )
            self.query_one(SDRmonHeader).gain = message.gain
            self._update_device_info()
            self.query_one(EventLog).log(f"Gain → {message.gain:.1f} dB", "info")
        except Exception as e:
            self.query_one(EventLog).log(f"Gain error: {e}", "error")

    def on_rate_changed(self, message: Any) -> None:
        if not self.controller or self.device.info.driver == "replay":
            return
        try:
            self.device.set_sample_rate(message.rate)
            self.controller.config = StreamConfig(
                frequency=self.controller.config.frequency,
                sample_rate=message.rate,
                gain=self.controller.config.gain,
            )
            self.query_one(SDRmonHeader).sample_rate = message.rate
            self._update_device_info()
            self.query_one(EventLog).log(f"Rate → {fmt_rate(message.rate)}", "info")
        except Exception as e:
            self.query_one(EventLog).log(f"Rate error: {e}", "error")

    def on_spectrum_click(self, message: SpectrumClick) -> None:
        if not self.controller or self.device.info.driver == "replay":
            return
        try:
            hz = message.freq_hz

            # ChannelManager only has 1 channel for now, we will update its frequency
            mgr = self.controller.channel_manager

            if not mgr.channels:
                # Add default channel if missing
                from sdrmon.dsp.channel import Channel

                ch = Channel(
                    "NFM",
                    hz,
                    self.controller.config.sample_rate,
                    self.controller.audio_rate,
                )
                mgr.add_channel(ch)
            else:
                mgr.channels[0].frequency = hz
                mgr.channels[0].set_sdr_center(mgr.sdr_center)

            # Check if channel is within usable bandwidth
            current_sdr_center = self.controller.config.frequency
            sdr_rate = self.controller.config.sample_rate
            usable_bw = sdr_rate * 0.9  # 90% usable

            if abs(hz - current_sdr_center) > usable_bw / 2:
                # Out of bounds, retune SDR
                self.device.set_frequency(hz)
                self.controller.config = StreamConfig(
                    frequency=hz,
                    sample_rate=sdr_rate,
                    gain=self.controller.config.gain,
                )
                self.query_one(SDRmonHeader).frequency = hz
                self.query_one(EventLog).log(f"HW Tuned → {fmt_freq(hz)}", "success")
                mgr.set_sdr_center(hz)
            else:
                # In bounds, NCO handles it
                self.query_one(EventLog).log(f"DSP Tuned → {fmt_freq(hz)}", "info")

            self.query_one("#ctrl-freq").frequency = hz  # type: ignore[attr-defined]
            self._update_device_info()
        except Exception as e:
            self.query_one(EventLog).log(f"Tune error: {e}", "error")

    def on_audio_settings_changed(self, message: AudioSettingsChanged) -> None:
        if not self.controller:
            return
        mgr = self.controller.channel_manager
        if not mgr.channels:
            from sdrmon.dsp.channel import Channel

            ch = Channel(
                "NFM",
                self.controller.config.frequency,
                self.controller.config.sample_rate,
                self.controller.audio_rate,
            )
            mgr.add_channel(ch)

        ch = mgr.channels[0]
        try:
            if message.mode is not None:
                ch.mode = message.mode.upper()
                # recreate demod
                from sdrmon.dsp.demod import create_demodulator

                ch.demod = create_demodulator(ch.mode, ch.sdr_rate, ch.audio_rate)
            if message.squelch is not None:
                ch.squelch = message.squelch
            if message.volume is not None:
                ch.volume = message.volume
            if message.muted is not None:
                ch.muted = message.muted
            if message.device is not None:
                # Open new audio device
                self.controller.audio_out.close()
                if message.device.lower() == "null":
                    from sdrmon.audio.output import NullAudioOutput

                    self.controller.audio_out = NullAudioOutput()
                else:
                    try:
                        from sdrmon.audio.output import SoundDeviceAudioOutput

                        self.controller.audio_out = SoundDeviceAudioOutput()
                        dev_name = (
                            message.device
                            if message.device.lower() != "default"
                            else None
                        )
                        self.controller.audio_out.open(
                            dev_name, self.controller.audio_rate
                        )
                    except Exception as e:
                        self.query_one(EventLog).log(f"Audio open err: {e}", "error")
                self.controller.audio_out.start()
        except Exception as e:
            self.query_one(EventLog).log(f"Audio DSP err: {e}", "error")

    def on_stream_error_msg(self, message: Any) -> None:
        log = self.query_one(EventLog)
        if getattr(message, "is_audio", False):
            log.log(f"AUDIO ERROR: {message.error}", "error")
            self.app.notify(
                f"AUDIO ERROR: {message.error}", severity="error", timeout=5.0
            )
            return

        log.log(f"Hardware disconnect / stream error: {message.error}", "error")
        self.app.notify(f"SDR Error: {message.error}", severity="error", timeout=10.0)

        if self.controller:
            self.controller.stop()
        try:
            self.device.close()
        except Exception as e:
            log.log(f"Error closing device: {e}", "warning")

        try:
            hdr = self.query_one(SDRmonHeader)
            hdr.is_paused = True
            hdr.mode = AppMode.ERROR
            self._mode = AppMode.ERROR
        except Exception:
            pass

    def on_unmount(self) -> None:
        if self.controller:
            self.controller.stop()
        try:
            self.device.close()
        except Exception:
            pass
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
        self._update_device_info()
        self.query_one(EventLog).log(f"View: {_VIEW_LABELS[self._view_mode]}", "info")

    def action_zoom_in(self) -> None:
        spec = self.query_one("#spectrum", SpectrumWidget)
        wf = self.query_one("#waterfall", WaterfallWidget)
        if wf.has_focus:
            self._waterfall_zoom = min(32.0, self._waterfall_zoom * 2.0)
            wf.zoom = self._waterfall_zoom  # type: ignore[attr-defined]
        else:
            self._spectrum_zoom = min(32.0, self._spectrum_zoom * 2.0)
            spec.zoom = self._spectrum_zoom  # type: ignore[attr-defined]
        self._update_device_info()

    def action_zoom_out(self) -> None:
        spec = self.query_one("#spectrum", SpectrumWidget)
        wf = self.query_one("#waterfall", WaterfallWidget)
        if wf.has_focus:
            self._waterfall_zoom = max(1.0, self._waterfall_zoom / 2.0)
            wf.zoom = self._waterfall_zoom  # type: ignore[attr-defined]
        else:
            self._spectrum_zoom = max(1.0, self._spectrum_zoom / 2.0)
            spec.zoom = self._spectrum_zoom  # type: ignore[attr-defined]
        self._update_device_info()

    def action_scale_up(self) -> None:
        spec = self.query_one("#spectrum", SpectrumWidget)
        spec.manual_range = min(120.0, spec.manual_range + 20.0)
        spec.auto_scale_enabled = False
        self._update_device_info()

    def action_scale_down(self) -> None:
        spec = self.query_one("#spectrum", SpectrumWidget)
        spec.manual_range = max(20.0, spec.manual_range - 20.0)
        spec.auto_scale_enabled = False
        self._update_device_info()

    def action_auto_scale(self) -> None:
        spec = self.query_one("#spectrum", SpectrumWidget)
        spec.auto_scale_enabled = True
        self._update_device_info()

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
        self._update_device_info()

    def action_freq(self) -> None:
        try:
            self.query_one("#freq-input").focus()
        except Exception:
            pass

    def action_gain(self) -> None:
        try:
            self.query_one("#gain-slider").focus()
        except Exception:
            pass

    def action_rate(self) -> None:
        try:
            self.query_one("#rate-select").focus()
        except Exception:
            pass

    def action_help(self) -> None:
        self.app.push_screen(HelpModal())

    def action_device_select(self) -> None:
        """Open device selection modal."""
        from sdrmon.ui.screens.device_modal import DeviceModal

        def on_result(result: SDRDevice | str | None) -> None:
            if not result:
                return
            if result == "replay":
                self.action_replay()
            else:
                if self.controller:
                    self.controller.stop()
                self.app.switch_to_monitor(result)  # type: ignore[attr-defined]

        self.app.push_screen(DeviceModal(), on_result)

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
