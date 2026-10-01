"""
Custom Slider widget for SDRmon.
"""

from typing import TypeVar

from rich.segment import Segment
from textual.events import Click, MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.reactive import reactive
from textual.strip import Strip
from textual.widget import Widget

T = TypeVar("T", int, float)


class SliderChanged(Message):
    """Fired when the slider value changes."""

    def __init__(self, slider: "Slider", value: float) -> None:
        super().__init__()
        self.slider = slider
        self.value = value


class Slider(Widget):
    """A simple terminal slider widget."""

    can_focus = True

    value = reactive(0.0)
    min_value = reactive(0.0)
    max_value = reactive(100.0)

    DEFAULT_CSS = """
    Slider {
        height: 1;
        min-width: 10;
        background: $surface;
        color: $text;
    }
    Slider:focus {
        color: $accent;
    }
    """

    def __init__(
        self,
        min_value: float = 0.0,
        max_value: float = 100.0,
        value: float = 0.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self._dragging = False

    def validate_value(self, value: float) -> float:
        return max(self.min_value, min(self.max_value, value))

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        if width <= 0:
            return Strip([])

        style = self.rich_style

        # Calculate knob position
        span = self.max_value - self.min_value
        if span <= 0:
            pos = 0
        else:
            ratio = (self.value - self.min_value) / span
            pos = int(ratio * (width - 1))
            pos = max(0, min(width - 1, pos))

        segments = []
        for i in range(width):
            if i == pos:
                segments.append(Segment("●", style))
            else:
                segments.append(Segment("─", style))

        return Strip(segments)

    def _update_from_mouse(self, x: int) -> None:
        width = self.size.width
        if width <= 1:
            return

        ratio = x / (width - 1)
        ratio = max(0.0, min(1.0, ratio))

        span = self.max_value - self.min_value
        new_val = self.min_value + ratio * span

        if self.value != new_val:
            self.value = new_val
            self.post_message(SliderChanged(self, self.value))

    def on_mouse_down(self, event: MouseDown) -> None:
        self.focus()
        self.capture_mouse()
        self._dragging = True
        self._update_from_mouse(event.x)

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging:
            self._update_from_mouse(event.x)

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.release_mouse()
            self._update_from_mouse(event.x)

    def on_click(self, event: Click) -> None:
        # Just in case down/up misses
        pass
