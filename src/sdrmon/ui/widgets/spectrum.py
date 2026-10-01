"""
Spectrum rendering widget for Textual.
"""

import numpy as np
from rich.segment import Segment
from rich.style import Style
from textual.message import Message
from textual.reactive import reactive
from textual.strip import Strip
from textual.widget import Widget

from sdrmon.analysis.spectrum import SpectrumResult


class SpectrumUpdated(Message):
    """Sent when new spectrum data is available."""

    def __init__(self, result: SpectrumResult) -> None:
        super().__init__()
        self.result = result


class SpectrumWidget(Widget):
    """A terminal spectrum analyzer widget."""

    min_power: reactive[float] = reactive(-100.0)
    max_power: reactive[float] = reactive(0.0)
    zoom: reactive[float] = reactive(1.0)

    DEFAULT_CSS = """
    SpectrumWidget {
        width: 100%;
        height: 100%;
        background: $surface;
        color: $text;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._block_chars = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        # Smoothing states
        self._last_max_power = 0.0
        self._last_min_power = -100.0
        self.result: SpectrumResult | None = None
        self.auto_scale_enabled = True
        self.manual_range = 100.0
        self.manual_ref = 0.0

    def update_result(self, new_result: SpectrumResult) -> None:
        self.result = new_result
        if new_result is not None:
            if self.auto_scale_enabled:
                # Auto-scale
                power = new_result.power
                p_max = float(np.max(power))
                p_min = float(np.min(power))

                # Add some padding and hysteresis
                target_max = p_max + 10.0
                target_min = max(p_min - 10.0, -120.0)

                # Smoothly approach
                self.max_power = self._last_max_power * 0.9 + target_max * 0.1
                self.min_power = self._last_min_power * 0.9 + target_min * 0.1

                self.manual_ref = self.max_power
            else:
                self.max_power = self.manual_ref
                self.min_power = self.manual_ref - self.manual_range

            self._last_max_power = self.max_power
            self._last_min_power = self.min_power

            self.refresh()

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        height = self.size.height

        if height <= 2 or width <= 2 or self.result is None:
            return Strip([Segment(" " * width)])

        # Determine y axis bounds for drawing
        # The top line (y=0) corresponds to max_power
        # The bottom line (y=height-1) corresponds to min_power

        # We will draw the spectrum bars.
        # A bar height is proportional to the power.

        # We reserve 8 chars for the Y axis
        chart_width = max(1, width - 8)

        # Downsample the frequency data to chart width
        power = self.result.power
        # Apply zoom: show only the center portion
        if self.zoom > 1.0:
            n = len(power)
            keep = max(1, int(n / self.zoom))
            start = (n - keep) // 2
            power = power[start : start + keep]
        n_bins = len(power)
        if n_bins == 0:
            return Strip([Segment(" " * width)])

        # Aggregate bins (max-preserving)
        from sdrmon.ui.rendering import aggregate_spectrum

        downsampled = aggregate_spectrum(power, chart_width, self.min_power)

        # Draw the line
        segments = []
        style = self.rich_style

        # Calculate power thresholds for this line
        if y == height - 1:
            # Render frequency labels
            if self.result is None:
                return Strip([Segment(" " * width)])

            freqs = self.result.frequencies
            if len(freqs) == 0:
                return Strip([Segment(" " * width)])

            if self.zoom > 1.0:
                n = len(freqs)
                keep = max(1, int(n / self.zoom))
                start = (n - keep) // 2
                freqs = freqs[start : start + keep]

            f_min = freqs[0]
            f_max = freqs[-1]
            f_center = self.result.center_frequency

            def fmt(f):
                if f >= 1e9:
                    return f"{f / 1e9:.1f}G"
                if f >= 1e6:
                    return f"{f / 1e6:.1f}M"
                if f >= 1e3:
                    return f"{f / 1e3:.1f}k"
                return f"{f}H"

            s_min = fmt(f_min)
            s_max = fmt(f_max)
            s_cen = fmt(f_center)

            # Simple layout
            line = " " * chart_width
            # Left align min
            line = s_min + line[len(s_min) :]
            # Center align cen
            cen_pos = max(0, chart_width // 2 - len(s_cen) // 2)
            line = line[:cen_pos] + s_cen + line[cen_pos + len(s_cen) :]
            # Right align max
            max_pos = chart_width - len(s_max)
            if max_pos > cen_pos + len(s_cen):
                line = line[:max_pos] + s_max

            # If there's a peak, also show it on the top line? Let's just return the strip
            return Strip([Segment(" " * 8 + line, Style(color="yellow"))])

        # Draw the spectrum bars
        # Adjust height because we stole 1 line for labels
        usable_height = height - 1

        power_range = self.max_power - self.min_power
        if power_range <= 0:
            power_range = 1.0

        power_per_row = power_range / usable_height
        power_top = self.max_power - (y * power_per_row)
        power_bottom = power_top - power_per_row

        for i, p in enumerate(downsampled):
            if p >= power_top:
                # Fully filled
                segments.append(Segment("█", style))
            elif p <= power_bottom:
                # Empty
                segments.append(Segment(" ", style))
            else:
                # Partially filled
                ratio = (p - power_bottom) / power_per_row
                char_idx = int(ratio * len(self._block_chars))
                char_idx = max(0, min(len(self._block_chars) - 1, char_idx))
                segments.append(Segment(self._block_chars[char_idx], style))

        # Build Y-axis prefix
        prefix = "        "
        if y % 4 == 0 or y == 0 or y == usable_height - 1:
            val = int(power_top)
            prefix = f"{val:4d} dB ┤"
            if len(prefix) > 8:
                prefix = prefix[-8:]
            elif len(prefix) < 8:
                prefix = prefix.rjust(8)

        segments.insert(0, Segment(prefix, Style(color="cyan")))

        return Strip(segments)
