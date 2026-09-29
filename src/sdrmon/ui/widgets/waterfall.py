"""
Waterfall rendering widget for Textual.
"""

from typing import Optional

import numpy as np
from rich.segment import Segment
from rich.style import Style
from textual.reactive import reactive
from textual.strip import Strip
from textual.widget import Widget

from sdrmon.analysis.spectrum import SpectrumResult
from sdrmon.ui.rendering import aggregate_spectrum, normalize_power


class WaterfallWidget(Widget):
    """A scrolling waterfall visualization."""

    # History size
    history_depth: reactive[int] = reactive(100)

    # Power bounds for color mapping
    min_power: reactive[float] = reactive(-100.0)
    max_power: reactive[float] = reactive(0.0)

    DEFAULT_CSS = """
    WaterfallWidget {
        width: 100%;
        height: 100%;
        background: $surface;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # buffer shape: (history_depth, display_width)
        # We store uint8 values from 0-255 mapped to a color scale
        self._buffer: Optional[np.ndarray] = None
        self._head = 0  # Points to the oldest row (next to write)
        self._display_width = 0

        # Color palette (0-255 mapping)
        # We will generate a palette of Rich Styles
        self._styles = self._generate_palette()

        # Smoothing states for power bounds
        self._last_max_power = 0.0
        self._last_min_power = -100.0

    def _generate_palette(self) -> list[Style]:
        """Generate a color gradient for the waterfall."""
        # A simple gradient from dark blue -> blue -> green -> yellow -> red
        # For simplicity, we just use 256 colors using rgb
        styles = []
        for i in range(256):
            # Map 0-255 to a heatmap
            if i < 64:
                # Black to Dark Blue
                r, g, b = 0, 0, int((i / 63.0) * 255)
            elif i < 128:
                # Dark Blue to Cyan
                val = (i - 64) / 63.0
                r, g, b = 0, int(val * 255), 255
            elif i < 192:
                # Cyan to Yellow
                val = (i - 128) / 63.0
                r, g, b = int(val * 255), 255, int((1.0 - val) * 255)
            else:
                # Yellow to Red
                val = (i - 192) / 63.0
                r, g, b = 255, int((1.0 - val) * 255), 0

            styles.append(Style(color=f"rgb({r},{g},{b})", bgcolor=f"rgb({r},{g},{b})"))
        return styles

    def _resize_buffer(self, width: int):
        if self._buffer is None or self._buffer.shape[1] != width:
            self._buffer = np.zeros((self.history_depth, width), dtype=np.uint8)
            self._display_width = width
            self._head = 0

    def update_result(self, result: SpectrumResult) -> None:
        if result is None:
            return

        width = self.size.width
        if width <= 0:
            return

        self._resize_buffer(width)

        power = result.power
        p_max = float(np.max(power))
        p_min = float(np.min(power))

        # Add padding and hysteresis
        target_max = p_max + 10.0
        target_min = max(p_min - 10.0, -120.0)

        # Smoothly approach
        self.max_power = self._last_max_power * 0.9 + target_max * 0.1
        self.min_power = self._last_min_power * 0.9 + target_min * 0.1

        self._last_max_power = self.max_power
        self._last_min_power = self.min_power

        # Aggregate down to terminal width
        downsampled = aggregate_spectrum(power, width, self.min_power)

        # Normalize to 0-255 uint8
        row = normalize_power(downsampled, self.min_power, self.max_power)

        # Write to ring buffer
        if self._buffer is not None:
            self._buffer[self._head, :] = row
            self._head = (self._head + 1) % self.history_depth

        self.refresh()

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        height = self.size.height

        if self._buffer is None or width <= 0 or height <= 0:
            return Strip([Segment(" " * width)])

        # The bottom line (y = height - 1) is the newest data
        # The top line (y = 0) is the oldest data

        # How many rows of the buffer are we displaying?
        # We only display up to `height` rows, taken from the newest entries.
        # So y=0 should correspond to the (newest - height + 1) entry
        # y=height-1 should correspond to the newest entry

        # Newest entry index in ring buffer:
        newest_idx = (self._head - 1) % self.history_depth

        # Calculate offset from newest
        # row_age = 0 is newest, row_age = height - 1 is oldest visible
        row_age = (height - 1) - y

        if row_age >= self.history_depth:
            # We don't have history that deep
            return Strip([Segment(" " * width)])

        # Index in ring buffer
        buf_idx = (newest_idx - row_age) % self.history_depth

        row_data = self._buffer[buf_idx]

        # If the width shrank between update and render, truncate safely
        if len(row_data) > width:
            row_data = row_data[:width]

        segments = []
        for val in row_data:
            # Full block char since we colored the background and foreground
            segments.append(Segment("█", self._styles[val]))

        # Pad if terminal grew
        if len(segments) < width:
            segments.append(Segment(" " * (width - len(segments))))

        return Strip(segments)
