"""
Reusable SDRmon UI components.

Header, Footer, Modal base, Select list, Buttons, EventLog.
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

# ── Application state ────────────────────────────────────────────────────────


class AppMode:
    DEVICE_SELECT = "device_select"
    LIVE = "live"
    REPLAY = "replay"
    SCANNER = "scanner"
    CAPTURE = "capture"
    SETTINGS = "settings"
    HELP = "help"


# ── Helpers ──────────────────────────────────────────────────────────────────


def fmt_freq(hz: float | int | None) -> str:
    if hz is None:
        return "N/A"
    if hz >= 1e9:
        return f"{hz / 1e9:.3f} GHz"
    if hz >= 1e6:
        return f"{hz / 1e6:.3f} MHz"
    if hz >= 1e3:
        return f"{hz / 1e3:.3f} kHz"
    return f"{int(hz)} Hz"


def fmt_rate(hz: float | int | None) -> str:
    if hz is None:
        return "N/A"
    if hz >= 1e6:
        return f"{hz / 1e6:.3f} MS/s"
    if hz >= 1e3:
        return f"{hz / 1e3:.3f} kS/s"
    return f"{int(hz)} S/s"


def parse_freq(val: str) -> int | None:
    """Parse human-readable frequency (e.g. '100M', '2.4G', '433k') to Hz."""
    val = val.strip().lower()
    if not val:
        return None
    mult = 1
    if val.endswith("g"):
        mult = 1_000_000_000
        val = val[:-1]
    elif val.endswith("m"):
        mult = 1_000_000
        val = val[:-1]
    elif val.endswith("k"):
        mult = 1_000
        val = val[:-1]
    try:
        return int(float(val) * mult)
    except ValueError:
        return None


# ── Status indicators ────────────────────────────────────────────────────────


def status_pill(mode: str, is_paused: bool = False, is_recording: bool = False) -> str:
    if is_recording:
        return "◉ RECORDING"
    if is_paused:
        return "◌ PAUSED"
    if mode == AppMode.LIVE:
        return "● LIVE"
    if mode == AppMode.REPLAY:
        return "▶ REPLAY"
    if mode == AppMode.SCANNER:
        return "⟳ SCANNING"
    return "○ IDLE"


def status_pill_class(
    mode: str, is_paused: bool = False, is_recording: bool = False
) -> str:
    if is_recording:
        return "pill-recording"
    if is_paused:
        return "pill-paused"
    if mode in (AppMode.LIVE, AppMode.SCANNER):
        return "pill-running"
    if mode == AppMode.REPLAY:
        return "pill-replay"
    return "pill-idle"


# ── SDRmon Header ─────────────────────────────────────────────────────────────


class SDRmonHeader(Widget):
    """Compact persistent header bar."""

    DEFAULT_CSS = """
    SDRmonHeader {
        height: 1;
        background: #0d47a1;
        color: #eceff1;
        padding: 0 1;
        layout: horizontal;
    }
    SDRmonHeader > #hdr-left {
        width: 1fr;
        content-align: left middle;
    }
    SDRmonHeader > #hdr-right {
        width: auto;
        content-align: right middle;
    }
    """

    mode: reactive[str] = reactive(AppMode.DEVICE_SELECT)
    device_name: reactive[str] = reactive("")
    frequency: reactive[int] = reactive(0)
    sample_rate: reactive[int] = reactive(0)
    gain: reactive[float | str] = reactive(0.0)
    is_paused: reactive[bool] = reactive(False)
    is_recording: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static("", id="hdr-left")
        yield Static("", id="hdr-right")

    def _build_left(self) -> str:
        parts = ["[bold]SDRMON[/bold]"]
        if self.mode == AppMode.LIVE:
            parts.append("[#00b0ff]LIVE[/#00b0ff]")
        elif self.mode == AppMode.REPLAY:
            parts.append("[#00b0ff]REPLAY[/#00b0ff]")
        elif self.mode == AppMode.SCANNER:
            parts.append("[#00b0ff]SCANNER[/#00b0ff]")

        if self.device_name:
            parts.append(self.device_name)

        if self.mode in (AppMode.LIVE, AppMode.REPLAY) and self.frequency:
            parts.append(fmt_freq(self.frequency))

        if self.mode in (AppMode.LIVE, AppMode.REPLAY) and self.sample_rate:
            parts.append(fmt_rate(self.sample_rate))

        if self.mode == AppMode.LIVE and self.gain:
            if isinstance(self.gain, str):
                parts.append(f"GAIN {self.gain}")
            else:
                parts.append(f"GAIN {self.gain:.0f} dB")

        return " │ ".join(parts)

    def _build_right(self) -> str:
        pill = status_pill(self.mode, self.is_paused, self.is_recording)
        css_class = status_pill_class(self.mode, self.is_paused, self.is_recording)
        color_map = {
            "pill-running": "#00e676",
            "pill-paused": "#ffea00",
            "pill-error": "#ff1744",
            "pill-recording": "#ff6d00",
            "pill-replay": "#00b0ff",
            "pill-idle": "#546e7a",
        }
        color = color_map.get(css_class, "#eceff1")
        return f"[{color}]{pill}[/{color}]"

    def _refresh_header(self) -> None:
        try:
            self.query_one("#hdr-left", Static).update(self._build_left())
            self.query_one("#hdr-right", Static).update(self._build_right())
        except Exception:
            pass

    def watch_mode(self, _: str) -> None:
        self._refresh_header()

    def watch_device_name(self, _: str) -> None:
        self._refresh_header()

    def watch_frequency(self, _: int) -> None:
        self._refresh_header()

    def watch_sample_rate(self, _: int) -> None:
        self._refresh_header()

    def watch_gain(self, _: float | str) -> None:
        self._refresh_header()

    def watch_is_paused(self, _: bool) -> None:
        self._refresh_header()

    def watch_is_recording(self, _: bool) -> None:
        self._refresh_header()

    def on_mount(self) -> None:
        self._refresh_header()


# ── SDRmon Footer ─────────────────────────────────────────────────────────────


class SDRmonFooter(Widget):
    """Persistent keyboard shortcut bar at the bottom."""

    DEFAULT_CSS = """
    SDRmonFooter {
        height: 1;
        background: #0d47a1;
        color: #b0bec5;
        padding: 0 1;
        layout: horizontal;
        content-align: left middle;
    }
    """

    shortcuts: reactive[list[tuple[str, str]]] = reactive([])

    def compose(self) -> ComposeResult:
        yield Static("", id="footer-content")

    def watch_shortcuts(self, value: list[tuple[str, str]]) -> None:
        try:
            parts = []
            for key, label in value:
                parts.append(f"[#1e88e5]{key}[/#1e88e5] {label}")
            self.query_one("#footer-content", Static).update("  ".join(parts))
        except Exception:
            pass

    def on_mount(self) -> None:
        self.watch_shortcuts(self.shortcuts)


LIVE_SHORTCUTS: list[tuple[str, str]] = [
    ("f", "Freq"),
    ("g", "Gain"),
    ("s", "Rate"),
    ("+/-", "Zoom"),
    ("v", "View"),
    ("c", "Capture"),
    ("r", "Replay"),
    ("S", "Scan"),
    ("d", "Device"),
    ("space", "Pause"),
    ("?", "Help"),
    ("q", "Quit"),
]

DEVICE_SHORTCUTS: list[tuple[str, str]] = [
    ("↑↓", "Select"),
    ("Enter", "Open"),
    ("F", "FakeSDR"),
    ("p", "Replay"),
    ("r", "Refresh"),
    ("q", "Quit"),
]

SCANNER_SHORTCUTS: list[tuple[str, str]] = [
    ("Enter", "Start"),
    ("space", "Pause"),
    ("c", "Cancel"),
    ("Esc", "Back"),
    ("q", "Quit"),
]

REPLAY_SHORTCUTS: list[tuple[str, str]] = [
    ("space", "Pause"),
    ("r", "Restart"),
    ("l", "Loop"),
    ("+/-", "Speed"),
    ("Esc", "Back"),
    ("q", "Quit"),
]


# ── Modal base ────────────────────────────────────────────────────────────────


class SDRmonModal(ModalScreen):  # type: ignore[type-arg]
    """Base modal dialog with SDRmon styling."""

    DEFAULT_CSS = """
    SDRmonModal {
        align: center middle;
        background: #0a0e14 70%;
    }
    .modal-dialog {
        width: 60;
        height: auto;
        border: solid #00b0ff;
        background: #1a2332;
        padding: 1 2;
    }
    .modal-title {
        text-style: bold;
        color: #00b0ff;
        margin-bottom: 1;
    }
    .modal-hint {
        color: #546e7a;
        margin-top: 1;
    }
    .btn-row {
        layout: horizontal;
        height: 3;
        align: right middle;
        margin-top: 1;
    }
    Button {
        margin-left: 1;
    }
    Button.btn-primary {
        background: #1e88e5;
        color: #eceff1;
    }
    Button.btn-cancel {
        background: #263238;
        color: #b0bec5;
    }
    """


# ── Frequency Modal ───────────────────────────────────────────────────────────


class FrequencyModal(SDRmonModal):
    """Modal dialog for setting center frequency."""

    def __init__(self, current_hz: int, readonly: bool = False, **kwargs: Any):
        super().__init__(**kwargs)
        self._current = current_hz
        self._readonly = readonly

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("SET FREQUENCY", classes="modal-title")
            if self._readonly:
                yield Label(
                    f"[#546e7a]Frequency is metadata in Replay mode.[/#546e7a]\n"
                    f"Current: {fmt_freq(self._current)}"
                )
            else:
                yield Label(f"Current: {fmt_freq(self._current)}")
                yield Input(
                    value=fmt_freq(self._current),
                    placeholder="e.g. 100M, 433.92M, 915M, 1.3G",
                    id="freq-input",
                )
                yield Label(
                    "Examples: 100M  433.92M  915M  2.437G",
                    classes="modal-hint",
                )
            with Horizontal(classes="btn-row"):
                yield Button("Cancel", id="btn-cancel", classes="btn-cancel")
                if not self._readonly:
                    yield Button("Apply", id="btn-apply", classes="btn-primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-apply":
            raw = self.query_one("#freq-input", Input).value
            hz = parse_freq(raw)
            if hz is None or hz <= 0:
                self.notify("Invalid frequency", severity="error")
                return
            self.dismiss(hz)

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss(None)


# ── Gain Modal ────────────────────────────────────────────────────────────────


class GainModal(SDRmonModal):
    """Modal dialog for setting gain."""

    def __init__(
        self,
        current: float | str,
        gain_values: list[float] | None = None,
        supported: bool = True,
        readonly: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._current = current
        self._gain_values = gain_values
        self._supported = supported
        self._readonly = readonly

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("GAIN", classes="modal-title")

            if self._readonly:
                yield Label(
                    f"[#546e7a]Gain is metadata in Replay mode.[/#546e7a]\n"
                    f"Current: {self._current}"
                )
            elif not self._supported:
                yield Label(
                    "[#546e7a]Gain control unavailable for this device.[/#546e7a]"
                )
            else:
                # Build choice list: AUTO + discrete values if available
                choices: list[str] = ["AUTO"]
                if self._gain_values:
                    choices += [f"{g:.1f} dB" for g in self._gain_values]
                else:
                    # Generic list for devices without discrete steps
                    choices += ["0.0 dB", "10.0 dB", "20.0 dB", "30.0 dB", "40.0 dB"]

                items = []
                for i, c in enumerate(choices):
                    item = ListItem(Label(c))
                    items.append(item)

                lv = ListView(*items, id="gain-list")
                yield lv

                # Scroll to active choice
                if isinstance(self._current, str) and self._current.lower() == "auto":
                    lv.index = 0
                elif self._gain_values:
                    try:
                        idx = self._gain_values.index(float(self._current)) + 1
                        lv.index = idx
                    except (ValueError, TypeError):
                        pass

            with Horizontal(classes="btn-row"):
                yield Button("Cancel", id="btn-cancel", classes="btn-cancel")
                if not self._readonly and self._supported:
                    yield Button("Apply", id="btn-apply", classes="btn-primary")

    def _choices(self) -> list[str]:
        choices: list[str] = ["AUTO"]
        if self._gain_values:
            choices += [f"{g:.1f} dB" for g in self._gain_values]
        else:
            choices += ["0.0 dB", "10.0 dB", "20.0 dB", "30.0 dB", "40.0 dB"]
        return choices

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-apply":
            lv = self.query_one("#gain-list", ListView)
            idx = lv.index
            if idx is None:
                self.dismiss(None)
                return
            choices = self._choices()
            selected = choices[idx]
            if selected == "AUTO":
                self.dismiss("auto")
            else:
                try:
                    value = float(selected.replace(" dB", ""))
                    self.dismiss(value)
                except ValueError:
                    self.dismiss(None)

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss(None)


# ── Sample Rate Modal ─────────────────────────────────────────────────────────

# Common RTL-SDR friendly sample rates shown as fallback
_COMMON_RATES = [
    250_000,
    1_024_000,
    1_800_000,
    2_000_000,
    2_048_000,
    2_400_000,
    2_560_000,
    3_200_000,
]


class SampleRateModal(SDRmonModal):
    """Modal dialog for selecting sample rate."""

    def __init__(
        self,
        current: int,
        sample_rates: list[int] | None = None,
        readonly: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._current = current
        self._rates = sample_rates if sample_rates else _COMMON_RATES
        self._readonly = readonly

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("SAMPLE RATE", classes="modal-title")

            if self._readonly:
                yield Label(
                    f"[#546e7a]Sample rate is metadata in Replay mode.[/#546e7a]\n"
                    f"Current: {fmt_rate(self._current)}"
                )
            else:
                items = [ListItem(Label(fmt_rate(r))) for r in self._rates]
                lv = ListView(*items, id="rate-list")
                yield lv
                # Scroll to active
                if self._current in self._rates:
                    lv.index = self._rates.index(self._current)

            with Horizontal(classes="btn-row"):
                yield Button("Cancel", id="btn-cancel", classes="btn-cancel")
                if not self._readonly:
                    yield Button("Apply", id="btn-apply", classes="btn-primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-apply":
            lv = self.query_one("#rate-list", ListView)
            idx = lv.index
            if idx is None or idx >= len(self._rates):
                self.dismiss(None)
                return
            self.dismiss(self._rates[idx])

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss(None)


# ── Help Modal ────────────────────────────────────────────────────────────────

_HELP_TEXT = """\
[bold #00b0ff]SDRMON KEYBOARD SHORTCUTS[/bold #00b0ff]

[#1e88e5]q[/#1e88e5]          Quit application
[#1e88e5]d[/#1e88e5]          Select / switch device
[#1e88e5]f[/#1e88e5]          Set center frequency
[#1e88e5]g[/#1e88e5]          Gain control
[#1e88e5]s[/#1e88e5]          Sample rate
[#1e88e5]+/-[/#1e88e5]        Display zoom
[#1e88e5]v[/#1e88e5]          Toggle Spectrum / Waterfall / Both
[#1e88e5]w[/#1e88e5]          Cycle FFT window
[#1e88e5]c[/#1e88e5]          Capture IQ to file
[#1e88e5]r[/#1e88e5]          Replay capture file
[#1e88e5]S[/#1e88e5]          Open RF Scanner
[#1e88e5]space[/#1e88e5]      Pause / Resume
[#1e88e5]l[/#1e88e5]          Toggle loop (Replay only)
[#1e88e5]?[/#1e88e5]          This help screen
[#1e88e5]Esc[/#1e88e5]        Back / close dialog
"""


class HelpModal(SDRmonModal):
    """Keyboard help modal."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(_HELP_TEXT)
            yield Label("[#546e7a]Esc or ? to close[/#546e7a]", classes="modal-hint")

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key in ("escape", "question_mark", "q"):
            self.dismiss(None)


# ── Event Log ─────────────────────────────────────────────────────────────────

MAX_LOG_ENTRIES = 50


class EventLog(Widget):
    """Bounded scrolling event log widget."""

    DEFAULT_CSS = """
    EventLog {
        height: 4;
        border: solid #1a3a5c;
        background: #0a0e14;
        overflow-y: auto;
        padding: 0 1;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._entries: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static("", id="log-content")

    def add_entry(self, msg: str, level: str = "info") -> None:
        color_map = {
            "info": "#b0bec5",
            "success": "#00e676",
            "warning": "#ffea00",
            "error": "#ff1744",
        }
        color = color_map.get(level, "#b0bec5")
        icon_map = {"info": "●", "success": "●", "warning": "!", "error": "!"}
        icon = icon_map.get(level, "●")
        entry = f"[{color}]{icon}[/{color}] {msg}"
        self._entries.append(entry)
        if len(self._entries) > MAX_LOG_ENTRIES:
            self._entries = self._entries[-MAX_LOG_ENTRIES:]
        self._redraw()

    # Convenience alias used by screens
    def log(self, msg: str, level: str = "info") -> None:  # type: ignore[override]
        self.add_entry(msg, level)

    def _redraw(self) -> None:
        try:
            content = "\n".join(self._entries[-8:])  # show last 8 visible
            self.query_one("#log-content", Static).update(content)
            self.scroll_end(animate=False)
        except Exception:
            pass
