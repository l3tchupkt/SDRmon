import asyncio
from sdrmon.ui.app import SDRmonApp
from sdrmon.native.manager import NativeSDRManager

async def test_ui_updates():
    manager = NativeSDRManager()
    dev = manager.open("fake:0")
    
    app = SDRmonApp(dev)
    async with app.run_test() as pilot:
        # Wait a bit for the worker to send messages
        await pilot.pause(2.0)
        
        # Check if the spectrum widget has a result
        from sdrmon.ui.widgets.spectrum import SpectrumWidget
        spec = app.screen.query_one(SpectrumWidget)
        if spec.result is not None:
            print("SUCCESS: SpectrumWidget received data!")
            print(f"Peak power: {spec.result.peak_power}")
        else:
            print("FAIL: SpectrumWidget has NO data.")

if __name__ == "__main__":
    asyncio.run(test_ui_updates())
