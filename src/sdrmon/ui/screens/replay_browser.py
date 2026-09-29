"""
Replay file browser screen.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from sdrmon.ui.components import AppMode, SDRmonFooter, SDRmonHeader


class ReplayBrowserScreen(Screen):
    """Screen to browse and select a .iq file for replay."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("q", "app.quit", "Quit"),
        ("enter", "open_selected", "Open"),
    ]

    DEFAULT_CSS = """
    ReplayBrowserScreen {
        background: #0a0e14;
    }
    #replay-body {
        margin: 1 4;
    }
    #path-row {
        height: 3;
        margin-bottom: 1;
    }
    ListView {
        height: 1fr;
        border: solid #1e88e5;
        background: #131920;
        margin-bottom: 1;
    }
    ListItem {
        height: 2;
        padding: 0 1;
    }
    #replay-buttons {
        height: 3;
    }
    Button {
        margin-right: 1;
    }
    #replay-status {
        height: 1;
        color: #546e7a;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_dir = Path.cwd()
        self._entries: list[Path] = []

    def compose(self) -> ComposeResult:
        hdr = SDRmonHeader(id="replay-header")
        hdr.mode = AppMode.REPLAY
        yield hdr
        with Vertical(id="replay-body"):
            yield Label("[bold #00b0ff]SELECT REPLAY FILE[/bold #00b0ff]")
            with Horizontal(id="path-row"):
                yield Label("Path:", id="path-label")
                yield Input(
                    value=str(self._current_dir),
                    id="path-input",
                    placeholder="Directory path",
                )
                yield Button("Browse", id="btn-browse")
            yield ListView(id="file-list")
            yield Static("", id="replay-status")
            with Horizontal(id="replay-buttons"):
                yield Button("▶ Open", id="btn-open", variant="primary")
                yield Button("↑ Parent", id="btn-parent")
                yield Button("← Back", id="btn-back")
        ftr = SDRmonFooter(id="replay-footer")
        ftr.shortcuts = [
            ("Enter", "Open"),
            ("↑↓", "Select"),
            ("Esc", "Back"),
            ("q", "Quit"),
        ]
        yield ftr

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
        except PermissionError:
            self.notify("Permission denied.", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open":
            self.action_open_selected()
        elif event.button.id == "btn-parent":
            self._load_directory(self._current_dir.parent)
        elif event.button.id == "btn-back":
            self.action_go_back()
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
        except Exception as e:
            self.notify(f"Failed to open: {e}", severity="error")
            return

        # Navigate to monitor
        try:
            self.app.switch_to_monitor(dev)  # type: ignore[attr-defined]
        except Exception:
            from sdrmon.ui.screens.monitor import MonitorScreen

            self.app.pop_screen()
            self.app.push_screen(MonitorScreen(dev))

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_open_selected()
