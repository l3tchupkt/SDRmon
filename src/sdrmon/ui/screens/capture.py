"""
Capture modal dialogs.
"""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label

from sdrmon.ui.components import SDRmonModal
from textual.message import Message


class CaptureErrorMsg(Message):
    """Fired when an error occurs during capture."""

    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error


class CaptureScreen(SDRmonModal):
    """A modal dialog to configure capture."""

    def __init__(self, default_path: str = "capture.iq", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.default_path = default_path

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("START CAPTURE", classes="modal-title")

            yield Label("File path", classes="modal-hint")
            yield Input(value=self.default_path, id="input-path")

            yield Label("Duration (seconds, optional)", classes="modal-hint")
            yield Input(
                placeholder="Leave empty for manual stop", id="input-duration"
            )

            with Horizontal(classes="btn-row"):
                yield Button("Cancel", id="btn-cancel", classes="btn-cancel")
                yield Button("Start Capture", id="btn-start", classes="btn-primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-start":
            path = self.query_one("#input-path", Input).value
            dur_str = self.query_one("#input-duration", Input).value

            dur = None
            if dur_str:
                try:
                    dur = float(dur_str)
                except ValueError:
                    self.notify("Invalid duration", severity="error")
                    return

            if not path:
                self.notify("Invalid path", severity="error")
                return

            self.dismiss({"path": path, "duration": dur})

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss(None)
