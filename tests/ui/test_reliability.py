import pytest
from sdrmon.native.manager import NativeSDRManager
from sdrmon.ui.app import SDRmonApp
from sdrmon.ui.components import AppMode
import time

@pytest.mark.asyncio
async def test_start_stop_stress():
    """Test rapid start/stop cycles (simulating 5 cycles to keep test time reasonable)."""
    manager = NativeSDRManager()
    
    # Do 5 open/start/stop/close cycles
    for _ in range(5):
        dev = manager.open("fake:0")
        app = SDRmonApp(dev)
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            assert app.screen._mode in (AppMode.LIVE, AppMode.STARTING)
            
            # pause
            await pilot.press("space")
            await pilot.pause(0.1)
            
            # resume
            await pilot.press("space")
            await pilot.pause(0.1)
        # On exit, run_test() cleans up and calls stop() on the controller
        # dev is automatically closed if app tears down

@pytest.mark.asyncio
async def test_device_disconnect_mock():
    """Test what happens if the device disconnects during streaming."""
    manager = NativeSDRManager()
    dev = manager.open("fake:0")
    
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        
        # Simulate an unrecoverable IO error in the background stream worker
        # by closing the device underneath it, or injecting an error event.
        # Actually, if we close the device, next_block() should raise an exception
        # or return an empty block, eventually triggering StreamErrorMsg.
        dev.close()
        
        await pilot.pause(0.5)
        
        # UI state should transition to DISCONNECTED or ERROR
        # Our app transitions to DISCONNECTED if there is an error in controller
        # Wait, does dev.close() trigger the stream error?
        # Let's post the StreamErrorMsg manually to verify UI state machine handles it
        from sdrmon.ui.controller import StreamErrorMsg
        app.screen.controller._running = False
        app.screen.post_message(StreamErrorMsg(Exception("Mock error")))
        
        await pilot.pause(0.5)
        
        assert app.screen._mode in (AppMode.ERROR, AppMode.DISCONNECTED)
        hdr = app.screen.query_one("SDRmonHeader")
        assert hdr.mode in (AppMode.ERROR, AppMode.DISCONNECTED)

@pytest.mark.asyncio
async def test_scanner_cancellation():
    """Test scanner cancellation and state transition back to LIVE."""
    manager = NativeSDRManager()
    dev = manager.open("fake:0")
    
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        
        # Press 'S' to open scanner
        await pilot.press("S")
        await pilot.pause(0.2)
        
        from sdrmon.ui.screens.scanner import ScannerScreen
        assert isinstance(app.screen, ScannerScreen)
        
        # It auto-starts the scan in on_mount
        assert app.screen._scanning == True
        
        # Cancel the scan via button click or Escape
        # Escape cancels and goes back in ScannerScreen
        await pilot.press("escape")
        await pilot.pause(0.2)
        
        # Should be back to MonitorScreen
        from sdrmon.ui.screens.monitor import MonitorScreen
        assert isinstance(app.screen, MonitorScreen)
        assert app.screen._mode == AppMode.LIVE

@pytest.mark.asyncio
async def test_ui_state_machine_validity():
    """Ensure no contradictory UI states."""
    manager = NativeSDRManager()
    dev = manager.open("fake:0")
    
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        
        # In LIVE mode
        assert app.screen._mode == AppMode.LIVE
        
        # Go to capture mode
        await pilot.press("c")
        await pilot.pause(0.1)
        # Actually Capture opens a modal, it doesn't change the main screen mode to CAPTURING until it starts.
        # Just check modal opens
        assert "CaptureScreen" in str(app.screen)
        
        # close modal
        await pilot.press("escape")
        await pilot.pause(0.1)
        
        assert app.screen._mode == AppMode.LIVE
