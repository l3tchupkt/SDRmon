"""
UI tests for SDRmonApp.

Tests use FakeSDR to avoid hardware dependencies.
"""

import pytest

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.ui.app import SDRmonApp
from sdrmon.ui.components import AppMode
from sdrmon.ui.screens.monitor import MonitorScreen, ViewMode
from sdrmon.ui.screens.startup import StartupScreen
from sdrmon.ui.widgets.spectrum import SpectrumWidget
from sdrmon.ui.widgets.waterfall import WaterfallWidget


def _fake_device(product: str = "FakeSDR") -> FakeSDRDevice:
    info = DeviceInfo(
        driver="fake",
        product=product,
        vendor="Virtual",
        serial="1",
        bus=None,
        usb_pid=None,
        usb_vid=None,
    )
    dev = FakeSDRDevice(info, seed=42)
    dev.open()
    return dev


# ── Startup screen ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_startup_screen_loads():
    """App without device shows startup screen."""
    app = SDRmonApp()
    async with app.run_test():
        # Startup screen should be active
        assert isinstance(app.screen, StartupScreen)
        # Device list should be present
        from textual.widgets import ListView

        lv = app.screen.query_one("#device-list", ListView)
        # Should have at least FakeSDR and Replay entries
        assert len(list(lv.children)) >= 2


@pytest.mark.asyncio
async def test_startup_fakesdr_selection():
    """Pressing F on startup screen launches FakeSDR monitor."""
    app = SDRmonApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, StartupScreen)
        # Press F to launch FakeSDR
        await pilot.press("f")
        await pilot.pause(0.3)
        # Should now show MonitorScreen
        assert isinstance(app.screen, MonitorScreen)
        # Clean up
        screen = app.screen
        if isinstance(screen, MonitorScreen) and screen.controller:
            screen.controller.stop()


# ── Monitor screen ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_monitor_with_device():
    """Passing a device directly launches monitor screen."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        assert isinstance(app.screen, MonitorScreen)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)
        assert screen.controller is not None

    dev.close()


@pytest.mark.asyncio
async def test_monitor_pause_resume():
    """Space bar pauses and resumes the stream."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)

        assert not screen.controller.is_paused()
        await pilot.press("space")
        assert screen.controller.is_paused()
        await pilot.press("space")
        assert not screen.controller.is_paused()

    dev.close()


@pytest.mark.asyncio
async def test_monitor_view_cycling():
    """v key cycles through Spectrum / Waterfall / Both."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)

        spec = app.screen.query_one("#spectrum", SpectrumWidget)
        wf = app.screen.query_one("#waterfall", WaterfallWidget)

        # Start in BOTH mode (default)
        assert screen._view_mode == ViewMode.BOTH

        await pilot.press("v")
        assert screen._view_mode == ViewMode.SPECTRUM
        assert not spec.has_class("hidden")
        assert wf.has_class("hidden")

        await pilot.press("v")
        assert screen._view_mode == ViewMode.WATERFALL
        assert spec.has_class("hidden")
        assert not wf.has_class("hidden")

        await pilot.press("v")
        assert screen._view_mode == ViewMode.BOTH

    dev.close()


@pytest.mark.asyncio
async def test_monitor_window_cycling():
    """w key cycles FFT window function."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)

        assert screen.controller.window == "hann"
        await pilot.press("w")
        assert screen.controller.window == "hamming"
        await pilot.press("w")
        assert screen.controller.window == "blackman"

    dev.close()


@pytest.mark.asyncio
async def test_monitor_zoom():
    """+ and - change display zoom."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)

        assert screen._zoom == 1.0
        await pilot.press("+")
        assert screen._zoom == 2.0
        await pilot.press("+")
        assert screen._zoom == 4.0
        await pilot.press("-")
        assert screen._zoom == 2.0

    dev.close()


@pytest.mark.asyncio
async def test_monitor_help_modal():
    """? opens help modal."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        from sdrmon.ui.components import HelpModal

        await pilot.press("question_mark")
        await pilot.pause(0.1)
        # Help modal should be pushed
        assert isinstance(app.screen, HelpModal)
        await pilot.press("escape")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MonitorScreen)

    dev.close()


@pytest.mark.asyncio
async def test_monitor_freq_modal():
    """f opens frequency modal."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        from sdrmon.ui.components import FrequencyModal

        await pilot.press("f")
        await pilot.pause(0.1)
        assert isinstance(app.screen, FrequencyModal)
        await pilot.press("escape")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MonitorScreen)

    dev.close()


@pytest.mark.asyncio
async def test_monitor_gain_modal():
    """g opens gain modal."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        from sdrmon.ui.components import GainModal

        await pilot.press("g")
        await pilot.pause(0.1)
        assert isinstance(app.screen, GainModal)
        await pilot.press("escape")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MonitorScreen)

    dev.close()


@pytest.mark.asyncio
async def test_monitor_samplerate_modal():
    """s opens sample rate modal."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        from sdrmon.ui.components import SampleRateModal

        await pilot.press("s")
        await pilot.pause(0.1)
        assert isinstance(app.screen, SampleRateModal)
        await pilot.press("escape")
        await pilot.pause(0.1)
        assert isinstance(app.screen, MonitorScreen)

    dev.close()


@pytest.mark.asyncio
async def test_monitor_scanner_launches():
    """S key opens scanner screen."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        from sdrmon.ui.screens.scanner import ScannerScreen

        await pilot.press("S")
        await pilot.pause(0.3)
        assert isinstance(app.screen, ScannerScreen)
        # ESC back to monitor
        await pilot.press("escape")
        await pilot.pause(0.3)
        assert isinstance(app.screen, MonitorScreen)

    dev.close()


@pytest.mark.asyncio
async def test_monitor_device_select_back():
    """d key goes back to device selection."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        await pilot.press("d")
        await pilot.pause(0.3)
        # Should be back at startup
        assert isinstance(app.screen, StartupScreen)

    # Don't close dev since monitor cleaned it up


@pytest.mark.asyncio
async def test_controller_shutdown():
    """Controller stops cleanly on unmount."""
    dev = _fake_device()
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)
        ctrl = screen.controller
        assert ctrl is not None
        assert ctrl._running

    # After context manager exits, controller should be stopped
    assert not ctrl._running
    dev.close()


# ── Component tests ───────────────────────────────────────────────────────────


def test_fmt_freq():
    from sdrmon.ui.components import fmt_freq

    assert "GHz" in fmt_freq(1_200_000_000)
    assert "MHz" in fmt_freq(100_000_000)
    assert "kHz" in fmt_freq(150_000)
    assert "Hz" in fmt_freq(500)
    assert fmt_freq(None) == "N/A"


def test_fmt_rate():
    from sdrmon.ui.components import fmt_rate

    assert "MS/s" in fmt_rate(2_000_000)
    assert "kS/s" in fmt_rate(500_000)
    assert "S/s" in fmt_rate(100)


def test_parse_freq():
    from sdrmon.ui.components import parse_freq

    assert parse_freq("100M") == 100_000_000
    assert parse_freq("433.92M") == 433_920_000
    assert parse_freq("915M") == 915_000_000
    assert parse_freq("2.437G") == 2_437_000_000
    assert parse_freq("") is None
    assert parse_freq("notanumber") is None


def test_status_pill():
    from sdrmon.ui.components import status_pill

    assert "LIVE" in status_pill(AppMode.LIVE)
    assert "REPLAY" in status_pill(AppMode.REPLAY)
    assert "PAUSED" in status_pill(AppMode.LIVE, is_paused=True)
    assert "RECORDING" in status_pill(AppMode.LIVE, is_recording=True)
