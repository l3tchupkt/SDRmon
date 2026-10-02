import pytest
from textual.geometry import Offset

from sdrmon.native.manager import NativeSDRManager
from sdrmon.ui.app import SDRmonApp
from sdrmon.ui.components import AppMode


@pytest.mark.asyncio
async def test_ui_lifecycle_and_interaction():
    manager = NativeSDRManager()
    dev = manager.open("fake:0")

    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        # Give worker a moment to start and push events
        await pilot.pause(0.5)

        # Test keyboard shortcuts
        # Pause
        await pilot.press("space")
        await pilot.pause(0.1)
        assert app.screen.controller.is_paused()

        # Resume
        await pilot.press("space")
        await pilot.pause(0.1)
        assert not app.screen.controller.is_paused()

        # Focus Frequency Control
        await pilot.press("f")
        await pilot.pause(0.1)
        # Should focus freq input
        assert app.screen.query_one("#freq-input").has_focus

        # Zoom in/out via keyboard
        from sdrmon.ui.widgets.spectrum import SpectrumWidget

        # Click spectrum to blur input
        await pilot.click(SpectrumWidget)
        await pilot.pause(0.1)

        await pilot.press("+")
        await pilot.pause(0.1)
        assert app.screen._spectrum_zoom == 2.0

        await pilot.press("-")
        await pilot.pause(0.1)
        assert app.screen._spectrum_zoom == 1.0

        # Test mouse interaction (Spectrum tuning)
        from sdrmon.ui.widgets.spectrum import SpectrumWidget

        app.screen.query_one(SpectrumWidget)

        # Simulate click
        await pilot.click(SpectrumWidget, offset=Offset(20, 5))
        await pilot.pause(0.1)

        # Test mouse interaction (Spectrum zoom)

        await pilot.pause(0.1)
        # Zoom should be triggered via scroll

        # Open Device selector
        await pilot.press("d")
        await pilot.pause(0.1)
        assert "DeviceModal" in str(app.screen)
        await pilot.press("escape")

        # App state should have transitioned to LIVE if fake stream pushed
        hdr = app.screen.query_one("SDRmonHeader")
        assert hdr.mode in (AppMode.LIVE, AppMode.STARTING)

        # Worker cancellation should happen automatically on unmount
