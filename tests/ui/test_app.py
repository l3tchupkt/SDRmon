import pytest

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.ui.app import SDRmonApp


@pytest.mark.asyncio
async def test_app_startup():
    info = DeviceInfo(
        driver="fake",
        product="Fake",
        vendor="Fake",
        serial="1",
        bus=None,
        usb_pid=None,
        usb_vid=None,
    )
    dev = FakeSDRDevice(info, seed=42)
    dev.open()

    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        # Check title
        assert app.title == "SDRmon - Fake"

        # Give worker a moment to send a message
        await pilot.pause(0.5)

        # Test pause/resume action
        assert not app.controller.is_paused()
        await pilot.press("space")
        assert app.controller.is_paused()
        await pilot.press("space")
        assert not app.controller.is_paused()

        # Test window toggle
        await pilot.press("w")
        assert app.controller.window == "hamming"

        # Test toggle waterfall
        from sdrmon.ui.widgets.waterfall import WaterfallWidget

        waterfall = app.query_one(WaterfallWidget)
        assert waterfall.has_class("hidden")
        await pilot.press("v")
        assert not waterfall.has_class("hidden")

        # Explicitly test controller shutdown
        app.controller.stop()
        assert not app.controller._running
        assert app.controller._thread is None
        assert app.controller._stream is None

    dev.close()
