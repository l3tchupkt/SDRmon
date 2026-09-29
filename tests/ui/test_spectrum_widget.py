import numpy as np
import pytest
from textual.app import App, ComposeResult

from sdrmon.analysis.spectrum import SpectrumResult
from sdrmon.ui.widgets.spectrum import SpectrumUpdated, SpectrumWidget


class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield SpectrumWidget(id="spectrum")

    def on_spectrum_updated(self, message: SpectrumUpdated) -> None:
        self.query_one(SpectrumWidget).update_result(message.result)


@pytest.mark.asyncio
async def test_spectrum_widget_handles_result():
    app = DummyApp()
    async with app.run_test() as pilot:
        widget = app.query_one(SpectrumWidget)

        # Initially none
        assert widget.result is None

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

        # Post message
        app.post_message(SpectrumUpdated(result))
        await pilot.pause(0.1)

        assert widget.result is not None
        assert widget.result.peak_power == -10.0

        # Check auto scaling updated
        assert widget.max_power > -10.0
        assert widget.min_power <= -50.0
