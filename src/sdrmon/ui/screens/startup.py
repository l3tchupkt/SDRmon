"""
Startup screen — device discovery and selection.
"""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, ListItem, ListView, Static

from sdrmon.core.device import DeviceInfo
from sdrmon.ui.components import DEVICE_SHORTCUTS, AppMode, SDRmonFooter, SDRmonHeader

LOGO_ART = """\
[#00b0ff]

╔═══════╗ ╔═══════╗ ╔═══════╗
║ ╔═════╝ ║ ╔═══╗ ║ ║ ╔═══╗ ║ ╔═════════╗ ╔═══════╗ ╔═══════╗
║ ╚═════╗ ║ ║   ║ ║ ║ ╚═══╝ ║ ║ ╔═╗ ╔═╗ ║ ║ ╔═══╗ ║ ║ ╔═══╗ ║
╚═════╗ ║ ║ ║   ║ ║ ║ ╔═╗ ╔═╝ ║ ║ ║ ║ ║ ║ ║ ║   ║ ║ ║ ║   ║ ║
╔═════╝ ║ ║ ╚═══╝ ║ ║ ║ ║ ╚═╗ ║ ║ ║ ║ ║ ║ ║ ╚═══╝ ║ ║ ║   ║ ║
╚═══════╝ ╚═══════╝ ╚═╝ ╚═══╝ ╚═╝ ╚═╝ ╚═╝ ╚═══════╝ ╚═╝   ╚═╝

[/#00b0ff]"""

# ── Device list item ─────────────────────────────────────────────────────────

class DeviceEntry:
    """Wraps a DeviceInfo with display metadata."""

    def __init__(
        self,
        info: DeviceInfo | None,
        label: str,
        sub: str,
        is_fake: bool = False,
        is_replay: bool = False,
    ) -> None:
        self.info = info
        self.label = label
        self.sub = sub
        self.is_fake = is_fake
        self.is_replay = is_replay


def _build_entries(devices: list[DeviceInfo]) -> list[DeviceEntry]:
    # Sort: hardware first (driver != fake), fake second
    hw_devices = [d for d in devices if d.driver != "fake"]
    fake_devices = [d for d in devices if d.driver == "fake"]

    entries: list[DeviceEntry] = []
    for d in hw_devices:
        entries.append(
            DeviceEntry(info=d, label=f"{d.vendor} {d.product}", sub=d.device_id)
        )
    for d in fake_devices:
        entries.append(
            DeviceEntry(info=d, label=f"{d.vendor} {d.product}", sub=d.device_id)
        )

    # If no fake devices were discovered by the backend for some reason, provide a fallback.
    if not fake_devices:
        entries.append(
            DeviceEntry(
                info=None,
                label="FakeSDR",
                sub="Synthetic signal source",
                is_fake=True,
            )
        )

    entries.append(
        DeviceEntry(
            info=None,
            label="Replay",
            sub="IQ capture",
            is_replay=True,
        )
    )
    return entries


def _make_list_item(entry: DeviceEntry, idx: int) -> ListItem:
    # Use a clean single line to match the mock
    label_text = f" [bold]{entry.label:<12}[/bold] [#546e7a]· {entry.sub}[/#546e7a]"
    return ListItem(Static(label_text), id=f"dev-item-{idx}")


# ── Startup screen ────────────────────────────────────────────────────────────


class StartupScreen(Screen):
    """Full-screen device selection / launcher."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("f", "use_fake", "FakeSDR"),
        ("p", "use_replay", "Replay"),
        ("enter", "open_selected", "Open"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[DeviceEntry] = []

    def compose(self) -> ComposeResult:
        hdr = SDRmonHeader(id="startup-header")
        hdr.device_name = "v0.1.0"
        yield hdr

        with Vertical(id="startup-body"):
            with Vertical(id="startup-center"):
                yield Static(LOGO_ART, id="startup-logo")

                with Center():
                    yield Static(
                        "[bold]Terminal SDR Monitor[/bold]", id="startup-subtitle"
                    )
                with Center():
                    yield Static(
                        "Select an SDR interface to begin", id="startup-status"
                    )

                yield ListView(id="device-list")

                with Horizontal(id="startup-buttons"):
                    yield Button("START", id="btn-start", variant="primary")
                    yield Button("REFRESH", id="btn-refresh")
                    yield Button("QUIT", id="btn-quit", variant="error")

        ftr = SDRmonFooter(id="startup-footer")
        ftr.shortcuts = DEVICE_SHORTCUTS
        yield ftr

    DEFAULT_CSS = """
    StartupScreen {
        background: #0a0e14;
    }
    #startup-body {
        align: center middle;
        height: 1fr;
    }
    #startup-center {
        width: 70;
        height: auto;
        align: center top;
    }
    #startup-logo {
        text-align: center;
        margin-bottom: 2;
    }
    #startup-subtitle {
        color: #eceff1;
        margin-bottom: 1;
    }
    #startup-status {
        color: #546e7a;
        margin-bottom: 2;
    }
    ListView {
        width: 100%;
        height: auto;
        min-height: 5;
        max-height: 10;
        border: round #1e88e5;
        background: #131920;
        margin-bottom: 2;
    }
    ListItem {
        padding: 0 2;
        height: 1;
    }
    ListItem.--highlight {
        background: #1a2332;
    }
    ListItem > Static {
        height: 1;
    }
    #startup-buttons {
        width: 100%;
        height: 3;
        align: center middle;
    }
    Button {
        min-width: 14;
        margin: 0 2;
    }
    """

    def on_mount(self) -> None:
        hdr = self.query_one(SDRmonHeader)
        hdr.mode = AppMode.DEVICE_SELECT
        self._refresh_devices()

    @work(thread=True, exclusive=True)
    def _refresh_devices(self) -> None:
        self.app.call_from_thread(self._start_refresh_ui)
        try:
            from sdrmon.native.manager import NativeSDRManager

            mgr = NativeSDRManager()
            physical = mgr.discover()
        except Exception:
            physical = []
        self.app.call_from_thread(self._finish_refresh_ui, physical)

    def _start_refresh_ui(self) -> None:
        status = self.query_one("#startup-status", Static)
        status.update("[#ffea00]Scanning for devices…[/#ffea00]")
        lv = self.query_one("#device-list", ListView)
        lv.clear()

    def _finish_refresh_ui(self, physical: list[DeviceInfo]) -> None:
        status = self.query_one("#startup-status", Static)
        self._entries = _build_entries(physical)

        lv = self.query_one("#device-list", ListView)
        lv.clear()
        for idx, entry in enumerate(self._entries):
            lv.append(_make_list_item(entry, idx))

        status.update("[#546e7a]Select an SDR interface to begin[/#546e7a]")

        if lv.children:
            lv.index = 0

    def _selected_entry(self) -> DeviceEntry | None:
        lv = self.query_one("#device-list", ListView)
        idx = lv.index
        if idx is None or idx < 0 or idx >= len(self._entries):
            return None
        return self._entries[idx]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.action_open_selected()
        elif event.button.id == "btn-refresh":
            self.action_refresh()
        elif event.button.id == "btn-quit":
            self.action_quit()

    def action_quit(self) -> None:
        self.app.exit()

    def action_refresh(self) -> None:
        self._refresh_devices()

    def action_open_selected(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        if entry.is_fake:
            self.action_use_fake()
        elif entry.is_replay:
            self.action_use_replay()
        else:
            self._launch_device(entry)

    def action_use_fake(self) -> None:
        from sdrmon.native.manager import NativeSDRManager

        mgr = NativeSDRManager()
        try:
            dev = mgr.open("fake:0")
        except Exception as e:
            self.notify(f"FakeSDR failed: {e}", severity="error")
            return
        self.app.switch_to_monitor(dev)  # type: ignore[attr-defined]

    def action_use_replay(self) -> None:
        self.app.open_replay_browser()  # type: ignore[attr-defined]

    def _launch_device(self, entry: DeviceEntry) -> None:
        if entry.info is None or entry.info.bus is None:
            return
        try:
            from sdrmon.native.manager import NativeSDRManager

            mgr = NativeSDRManager()
            dev = mgr.open(entry.info.bus)
        except Exception as e:
            self.notify(f"Failed to open device: {e}", severity="error")
            return
            
        try:
            self.app.sdrmon_config.preferred_device = entry.info.bus # type: ignore
        except Exception:
            pass
            
        self.app.switch_to_monitor(dev)  # type: ignore[attr-defined]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Double-confirm via Enter activates open
        self.action_open_selected()
