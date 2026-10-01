"""
Scanner screen — full-screen RF scanner.
"""

from __future__ import annotations

from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button

from sdrmon.core.device import SDRDevice
from sdrmon.scanner import ScanConfig, Scanner, ScanResult
from sdrmon.ui.components import (
    SCANNER_SHORTCUTS,
    AppMode,
    EventLog,
    SDRmonFooter,
    SDRmonHeader,
    fmt_freq,
)
from sdrmon.ui.widgets.scanner import ScannerWidget


class ScanResultMsg(Message):
    def __init__(self, result: ScanResult) -> None:
        super().__init__()
        self.result = result


class ScanCompletedMsg(Message):
    pass


class ScanErrorMsg(Message):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error


class ScannerScreen(Screen):
    """Full-screen RF scanner."""

    BINDINGS = [
        ("c", "cancel_scan", "Cancel"),
        ("space", "cancel_scan", "Pause"),
        ("enter", "start_scan", "Start"),
        ("escape", "go_back", "Back"),
        ("q", "app.quit", "Quit"),
    ]

    DEFAULT_CSS = """
    ScannerScreen {
        background: #0a0e14;
        layout: vertical;
    }
    #scanner-widget {
        height: 1fr;
    }
    #scanner-log {
        height: 5;
        border-top: solid #1e88e5;
        background: #131920;
    }
    """

    def __init__(
        self, device: SDRDevice, config: ScanConfig, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.device = device
        self.config = config
        self.scanner = Scanner(self.device)
        self._scanning = False

    def compose(self) -> ComposeResult:
        hdr = SDRmonHeader(id="scanner-header")
        hdr.mode = AppMode.SCANNER
        hdr.device_name = self.device.info.product
        yield hdr

        yield ScannerWidget(id="scanner-widget")
        yield EventLog(id="scanner-log")

        ftr = SDRmonFooter(id="scanner-footer")
        ftr.shortcuts = SCANNER_SHORTCUTS
        yield ftr

    def on_mount(self) -> None:
        span = self.config.stop_frequency - self.config.start_frequency
        steps = max(1, int(span // self.config.step) + 1)
        widget = self.query_one(ScannerWidget)
        widget.update_config(self.config, steps)

        hdr = self.query_one(SDRmonHeader)
        hdr.mode = AppMode.SCANNER

        log = self.query_one(EventLog)
        log.log(
            f"Scanner ready: {fmt_freq(self.config.start_frequency)} → "
            f"{fmt_freq(self.config.stop_frequency)}, "
            f"step {fmt_freq(self.config.step)}",
            "info",
        )
        # Auto-start
        self.action_start_scan()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scan-start":
            self.action_start_scan()
        elif event.button.id == "btn-scan-cancel":
            self.action_cancel_scan()
        elif event.button.id == "btn-scan-back":
            self.action_go_back()

    def action_start_scan(self) -> None:
        if self._scanning:
            return
        self._scanning = True
        widget = self.query_one(ScannerWidget)
        widget.clear_results()
        self._scan_worker()
        self.query_one(EventLog).log("Scan started", "success")

    @work(thread=True)
    def _scan_worker(self) -> None:
        try:
            for result in self.scanner.scan(self.config):
                self.post_message(ScanResultMsg(result))
            self.post_message(ScanCompletedMsg())
        except Exception as e:
            self.post_message(ScanErrorMsg(e))

    def on_unmount(self) -> None:
        self.scanner.cancel()
        self._scanning = False

    def action_cancel_scan(self) -> None:
        self.scanner.cancel()
        self._scanning = False
        self.query_one(EventLog).log("Scan cancelled.", "warning")

    def action_go_back(self) -> None:
        self.scanner.cancel()
        self.app.pop_screen()

    def on_scan_result_msg(self, message: ScanResultMsg) -> None:
        widget = self.query_one(ScannerWidget)
        widget.add_result(message.result)

    def on_scan_completed_msg(self, _: ScanCompletedMsg) -> None:
        self._scanning = False
        self.query_one(EventLog).log("Scan complete.", "success")

    def on_scan_error_msg(self, message: ScanErrorMsg) -> None:
        self._scanning = False
        self.query_one(EventLog).log(f"Scan error: {message.error}", "error")
