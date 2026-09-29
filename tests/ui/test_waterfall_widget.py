import numpy as np
import pytest
from textual.app import App, ComposeResult

from sdrmon.analysis.spectrum import SpectrumResult
from sdrmon.ui.widgets.waterfall import WaterfallWidget


class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield WaterfallWidget(id="waterfall")


@pytest.mark.asyncio
async def test_waterfall_widget_empty():
    app = DummyApp()
    async with app.run_test():
        widget = app.query_one(WaterfallWidget)

        # Buffer should not be allocated until there's size and data
        assert widget._buffer is None

        # Force a render line, should be empty spaces
        line = widget.render_line(0)
        assert len(line) == 1
        assert " " in str(line._segments[0].text)


@pytest.mark.asyncio
async def test_waterfall_widget_result():
    app = DummyApp()
    async with app.run_test() as pilot:
        widget = app.query_one(WaterfallWidget)

        # Fake a result
        frequencies = np.linspace(99e6, 101e6, 2048, dtype=np.float64)
        power = np.full(2048, -50.0, dtype=np.float32)
        power[1024] = -10.0  # Peak

        result = SpectrumResult(
            frequencies=frequencies,
            power=power,
            peak_frequency=100e6,
            peak_power=-10.0,
            noise_floor=-50.0,
            center_frequency=100_000_000,
            sample_rate=2_000_000,
            timestamp=0.0,
        )

        widget.update_result(result)
        await pilot.pause(0.1)

        assert widget._buffer is not None
        assert widget._buffer.shape[0] == widget.history_depth
        assert widget._buffer.shape[1] == widget.size.width

        # The head advanced by 1
        assert widget._head == 1

        # The oldest is rendered at y=0. If history_depth=100 and height is e.g. 24
        # We only wrote 1 line, so it's going to be padded with 0s
        line = widget.render_line(widget.size.height - 1)
        # It's a Strip.
        assert len(line._segments) > 0
        # Peak should be somewhere in the middle (colored differently)
        # We can just verify it doesn't crash and returns segments
