"""
Startup screen — device discovery and selection.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, ListItem, ListView, Static

from sdrmon.core.device import DeviceInfo
from sdrmon.devices.manager import SDRManager
from sdrmon.ui.components import DEVICE_SHORTCUTS, AppMode, SDRmonFooter, SDRmonHeader

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
    entries: list[DeviceEntry] = []
    for d in devices:
        serial_part = f"  Serial: {d.serial}" if d.serial else ""
        sub = f"{d.driver}{serial_part}"
        entries.append(DeviceEntry(info=d, label=f"{d.vendor} {d.product}", sub=sub))
    # Always offer FakeSDR
    entries.append(
        DeviceEntry(
            info=None,
            label="FakeSDR",
            sub="Synthetic signal generator (no hardware required)",
            is_fake=True,
        )
    )
    # Always offer Replay
    entries.append(
        DeviceEntry(
            info=None,
            label="Replay Capture",
            sub="Open a previously recorded .iq file",
            is_replay=True,
        )
    )
    return entries


def _make_list_item(entry: DeviceEntry, idx: int) -> ListItem:
    icon = "●" if not (entry.is_fake or entry.is_replay) else "○"
    label_text = f"[bold]{icon} {entry.label}[/bold]\n[#546e7a]  {entry.sub}[/#546e7a]"
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
        self._physical_count = 0

    def compose(self) -> ComposeResult:
        yield SDRmonHeader(id="startup-header")
        with Vertical(id="startup-body"):
            yield Static(
                "[bold #00b0ff]  SDRmon[/bold #00b0ff]  "
                "[#546e7a]Terminal SDR Monitor[/#546e7a]",
                id="startup-logo",
            )
            yield Static("", id="startup-status")
            yield ListView(id="device-list")
            with Horizontal(id="startup-buttons"):
                yield Button("Start", id="btn-start", variant="primary")
                yield Button("FakeSDR", id="btn-fake")
                yield Button("Replay…", id="btn-replay")
                yield Button("Refresh", id="btn-refresh")
                yield Button("Quit", id="btn-quit", variant="error")
        hdr = SDRmonFooter(id="startup-footer")
        hdr.shortcuts = DEVICE_SHORTCUTS
        yield hdr

    DEFAULT_CSS = """
    StartupScreen {
        background: #0a0e14;
    }
    #startup-body {
        margin: 1 4;
    }
    #startup-logo {
        height: 2;
        margin-bottom: 1;
        color: #eceff1;
    }
    #startup-status {
        height: 1;
        color: #546e7a;
        margin-bottom: 1;
    }
    ListView {
        height: 1fr;
        border: solid #1e88e5;
        background: #131920;
        margin-bottom: 1;
    }
    ListItem {
        padding: 1;
        height: 4;
    }
    ListItem.--highlight {
        background: #1a2332;
    }
    ListItem > Static {
        height: auto;
    }
    #startup-buttons {
        height: 3;
        margin-top: 1;
    }
    Button {
        margin-right: 1;
    }
    """

    def on_mount(self) -> None:
        hdr = self.query_one(SDRmonHeader)
        hdr.mode = AppMode.DEVICE_SELECT
        self._refresh_devices()

    def _refresh_devices(self) -> None:
        status = self.query_one("#startup-status", Static)
        status.update("[#ffea00]Scanning for devices…[/#ffea00]")
        try:
            physical = SDRManager.discover()
        except Exception:
            physical = []

        self._physical_count = len(physical)
        self._entries = _build_entries(physical)

        lv = self.query_one("#device-list", ListView)
        lv.clear()
        for idx, entry in enumerate(self._entries):
            lv.append(_make_list_item(entry, idx))

        if physical:
            status.update(
                f"[#00e676]{len(physical)} device(s) found.[/#00e676]  "
                "Select a device and press Enter or [Start]."
            )
        else:
            status.update(
                "[#546e7a]No physical SDR devices detected. "
                "Use FakeSDR or Replay.[/#546e7a]"
            )

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
        elif event.button.id == "btn-fake":
            self.action_use_fake()
        elif event.button.id == "btn-replay":
            self.action_use_replay()
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
        from sdrmon.backends.generic.fake import FakeSDRDevice
        from sdrmon.core.device import DeviceInfo

        info = DeviceInfo(
            driver="fake",
            product="FakeSDR",
            vendor="Virtual",
            serial="1",
            bus=None,
            usb_pid=None,
            usb_vid=None,
        )
        dev = FakeSDRDevice(info, seed=42)
        try:
            dev.open()
        except Exception as e:
            self.notify(f"FakeSDR failed: {e}", severity="error")
            return
        self.app.switch_to_monitor(dev)  # type: ignore[attr-defined]

    def action_use_replay(self) -> None:
        self.app.open_replay_browser()  # type: ignore[attr-defined]

    def _launch_device(self, entry: DeviceEntry) -> None:
        if entry.info is None:
            return
        try:
            dev = SDRManager.open(entry.info)
        except Exception as e:
            self.notify(f"Failed to open device: {e}", severity="error")
            return
        self.app.switch_to_monitor(dev)  # type: ignore[attr-defined]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Double-confirm via Enter activates open
        self.action_open_selected()
