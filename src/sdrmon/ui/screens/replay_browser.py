"""
Replay file browser modal.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from sdrmon.ui.components import SDRmonModal


class ReplayModal(SDRmonModal):
    """Modal dialog to select a .iq file for replay."""

    DEFAULT_CSS = """
    ReplayModal {
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
    #path-row {
        height: 3;
        margin-bottom: 1;
    }
    ListView {
        height: 1fr;
        min-height: 5;
        max-height: 15;
        border: solid #1e88e5;
        background: #131920;
        margin-bottom: 1;
    }
    ListItem {
        height: 1;
        padding: 0 1;
    }
    ListItem.--highlight {
        background: #1a2332;
    }
    #replay-status {
        height: 1;
        color: #546e7a;
        margin-bottom: 1;
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
        self._current_dir = Path.cwd()
        self._entries: list[Path] = []

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("OPEN CAPTURE", classes="modal-title")
            with Horizontal(id="path-row"):
                yield Input(
                    value=str(self._current_dir),
                    id="path-input",
                    placeholder="Directory path",
                )
                yield Button("Browse", id="btn-browse")
            yield ListView(id="file-list")
            yield Static("", id="replay-status")
            with Horizontal(classes="btn-row"):
                yield Label("Enter Open   Esc Cancel", classes="modal-hint")
                yield Static("", classes="spacer", id="spacer-left")
                yield Button("↑ Parent", id="btn-parent", classes="btn-cancel")
                yield Button("Cancel", id="btn-back", classes="btn-cancel")
                yield Button("Open", id="btn-open", classes="btn-primary")

    def on_mount(self) -> None:
        self._load_directory(self._current_dir)

    def _load_directory(self, path: Path) -> None:
        try:
            self._current_dir = path
            self.query_one("#path-input", Input).value = str(path)
            entries: list[Path] = []
            for p in sorted(path.iterdir()):
                if p.is_dir():
                    entries.append(p)
                elif p.suffix.lower() in (".iq", ".bin", ".raw"):
                    entries.append(p)
            self._entries = entries
            lv = self.query_one("#file-list", ListView)
            lv.clear()
            for e in entries:
                icon = "📁 " if e.is_dir() else "📄 "
                lv.append(ListItem(Static(f"{icon}{e.name}")))
            status = self.query_one("#replay-status", Static)
            status.update(
                f"{len([e for e in entries if not e.is_dir()])} .iq file(s) in directory"
            )
            if lv.children:
                lv.index = 0
        except PermissionError:
            self.notify("Permission denied.", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open":
            self.action_open_selected()
        elif event.button.id == "btn-parent":
            self._load_directory(self._current_dir.parent)
        elif event.button.id == "btn-back":
            self.dismiss(None)
        elif event.button.id == "btn-browse":
            path_str = self.query_one("#path-input", Input).value
            new_path = Path(path_str)
            if new_path.is_dir():
                self._load_directory(new_path)
            else:
                self.notify("Not a valid directory", severity="error")

    def action_open_selected(self) -> None:
        lv = self.query_one("#file-list", ListView)
        idx = lv.index
        if idx is None or idx >= len(self._entries):
            return
        entry = self._entries[idx]
        if entry.is_dir():
            self._load_directory(entry)
        else:
            self._open_replay(entry)

    def _open_replay(self, path: Path) -> None:
        try:
            from sdrmon.capture.metadata import CaptureMetadata
            from sdrmon.core.device import DeviceInfo
            from sdrmon.replay.replay import ReplayDevice

            json_path = path.with_suffix(".json")
            if not json_path.exists():
                self.notify(
                    f"No metadata file found: {json_path.name}\n"
                    "Expected a .json file alongside the .iq file.",
                    severity="error",
                )
                return

            meta = CaptureMetadata.load(json_path)
            info = DeviceInfo(
                driver="replay",
                product=path.name,
                vendor="Replay",
                serial=None,
                bus=None,
                usb_vid=None,
                usb_pid=None,
            )
            dev = ReplayDevice(info, path, meta)
            dev.open()
            self.dismiss(dev)
        except Exception as e:
            self.notify(f"Failed to open: {e}", severity="error")
            return

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_open_selected()
