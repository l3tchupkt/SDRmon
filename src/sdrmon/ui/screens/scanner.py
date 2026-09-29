"""
Scanner screen.
"""

import threading
from typing import Optional

from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header

from sdrmon.core.device import SDRDevice
from sdrmon.scanner import ScanConfig, Scanner, ScanResult
from sdrmon.ui.widgets.scanner import ScannerWidget


class ScanResultMsg(Message):
    """Fired when the background scanner yields a result."""

    def __init__(self, result: ScanResult):
        super().__init__()
        self.result = result


class ScanCompletedMsg(Message):
    """Fired when the background scanner finishes."""

    pass


class ScanErrorMsg(Message):
    """Fired when the background scanner errors."""

    def __init__(self, error: Exception):
        super().__init__()
        self.error = error


class ScannerScreen(Screen):
    """Screen for running and viewing RF scans."""

    BINDINGS = [
        ("c", "cancel_scan", "Cancel Scan"),
        ("escape", "app.pop_screen", "Back to Monitor"),
    ]

    def __init__(self, device: SDRDevice, config: ScanConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device
        self.config = config
        self.scanner = Scanner(self.device)
        self._thread: Optional[threading.Thread] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ScannerWidget(id="scanner-widget")
        yield Footer()

    def on_mount(self) -> None:
        span = self.config.stop_frequency - self.config.start_frequency
        steps = int(span // self.config.step)
        if span % self.config.step != 0 or steps == 0:
            steps += 1
        total_steps = steps + 1

        widget = self.query_one(ScannerWidget)
        widget.update_config(self.config, total_steps)

        # Start background scanner thread
        self._thread = threading.Thread(target=self._scan_worker, daemon=True)
        self._thread.start()

    def _scan_worker(self):
        try:
            for result in self.scanner.scan(self.config):
                self.post_message(ScanResultMsg(result))
            self.post_message(ScanCompletedMsg())
        except Exception as e:
            self.post_message(ScanErrorMsg(e))

    def on_unmount(self) -> None:
        self.scanner.cancel()
        if self._thread:
            self._thread.join(timeout=2.0)

    def action_cancel_scan(self) -> None:
        self.scanner.cancel()
        self.notify("Scan cancelled.", severity="warning")

    def on_scan_result_msg(self, message: ScanResultMsg) -> None:
        widget = self.query_one(ScannerWidget)
        widget.add_result(message.result)

    def on_scan_completed_msg(self, message: ScanCompletedMsg) -> None:
        self.notify("Scan completed.", severity="information")

    def on_scan_error_msg(self, message: ScanErrorMsg) -> None:
        self.notify(f"Scan error: {message.error}", severity="error")
