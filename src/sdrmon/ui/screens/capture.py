"""
Capture screen and dialogs.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class CaptureErrorMsg(Message):
    """Fired when an error occurs during capture."""

    def __init__(self, error: Exception):
        super().__init__()
        self.error = error


class CaptureScreen(ModalScreen[Optional[dict]]):
    """A modal dialog to configure capture."""

    DEFAULT_CSS = """
    CaptureScreen {
        align: center middle;
        background: $background 50%;
    }
    #capture-dialog {
        width: 60;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }
    .input-row {
        height: 3;
        margin-bottom: 1;
    }
    .label {
        width: 15;
        padding-top: 1;
    }
    #buttons {
        height: auto;
        align: right middle;
        margin-top: 1;
    }
    Button {
        margin-left: 1;
    }
    """

    def __init__(self, default_path: str = "capture.iq", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_path = default_path

    def compose(self) -> ComposeResult:
        with Vertical(id="capture-dialog"):
            yield Label("[bold]START CAPTURE[/bold]", classes="title")

            with Horizontal(classes="input-row"):
                yield Label("File:", classes="label")
                yield Input(value=self.default_path, id="input-path")

            with Horizontal(classes="input-row"):
                yield Label("Duration (s):", classes="label")
                yield Input(
                    placeholder="Leave empty for manual stop", id="input-duration"
                )

            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Start", variant="success", id="btn-start")

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
