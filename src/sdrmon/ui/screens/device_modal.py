"""
Device selection modal.
"""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, ListItem, ListView, Static

from sdrmon.core.device import DeviceInfo
from sdrmon.devices.manager import SDRManager
from sdrmon.ui.components import SDRmonModal
from sdrmon.ui.screens.startup import DeviceEntry, _build_entries, _make_list_item


class DeviceModal(SDRmonModal):
    """Modal dialog for selecting an SDR device."""

    DEFAULT_CSS = """
    DeviceModal {
        align: center middle;
        background: #0a0e14 70%;
    }
    .modal-dialog {
        width: 70;
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
    ListView {
        width: 100%;
        height: auto;
        min-height: 5;
        max-height: 10;
        border: solid #1e88e5;
        background: #131920;
        margin-bottom: 1;
    }
    ListItem {
        padding: 0 1;
        height: 1;
    }
    ListItem.--highlight {
        background: #1a2332;
    }
    ListItem > Static {
        height: 1;
    }
    .btn-row {
        layout: horizontal;
        height: 3;
        align: right middle;
    }
    .spacer {
        width: 1fr;
    }
    Button {
        margin-left: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[DeviceEntry] = []

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("SELECT SDR DEVICE", classes="modal-title")
            yield ListView(id="device-list")
            with Horizontal(classes="btn-row"):
                yield Label("↑↓ Select   Enter Open   r Refresh   Esc Cancel", classes="modal-hint")
                yield Static("", classes="spacer", id="spacer-left")
                yield Button("Cancel", id="btn-cancel", classes="btn-cancel")
                yield Button("Open", id="btn-open", classes="btn-primary")

    def on_mount(self) -> None:
        self._refresh_devices()

    @work(thread=True, exclusive=True)
    def _refresh_devices(self) -> None:
        self.app.call_from_thread(self._show_loading)
        try:
            physical = SDRManager.discover()
        except Exception:
            physical = []
        self.app.call_from_thread(self._populate_list, physical)

    def _show_loading(self) -> None:
        lv = self.query_one("#device-list", ListView)
        lv.clear()
        lv.append(ListItem(Static("Discovering devices..."), id="loading-item"))

    def _populate_list(self, physical: list[DeviceInfo]) -> None:
        self._entries = _build_entries(physical)
        lv = self.query_one("#device-list", ListView)
        lv.clear()

        for idx, entry in enumerate(self._entries):
            lv.append(_make_list_item(entry, idx))

        if lv.children:
            lv.index = 0

    def _selected_entry(self) -> DeviceEntry | None:
        lv = self.query_one("#device-list", ListView)
        idx = lv.index
        if idx is None or idx < 0 or idx >= len(self._entries):
            return None
        return self._entries[idx]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-open":
            self.action_open_selected()

    def action_open_selected(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return

        if entry.is_fake:
            from sdrmon.backends.generic.fake import FakeSDRDevice
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
                self.dismiss(dev)
            except Exception as e:
                self.notify(f"FakeSDR failed: {e}", severity="error")

        elif entry.is_replay:
            # Replay requires another modal. Return a special string to indicate this
            self.dismiss("replay")

        else:
            if entry.info is None:
                return
            try:
                dev = SDRManager.open(entry.info)
                self.dismiss(dev)
            except Exception as e:
                self.notify(f"Failed to open device: {e}", severity="error")

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "r":
            self._refresh_devices()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_open_selected()
