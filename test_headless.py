import time
from sdrmon.core.settings import StreamConfig
from sdrmon.native.manager import NativeSDRManager
from sdrmon.ui.controller import UIController
from sdrmon.ui.widgets.spectrum import SpectrumUpdated

class DummyApp:
    def __init__(self):
        self.blocks = 0
        self.updates = 0
    def post_message(self, msg):
        if isinstance(msg, SpectrumUpdated):
            self.updates += 1
            print(f"Spectrum update {self.updates}: max power {msg.result.power.max():.2f}")
        else:
            print(f"App message: {msg}")

def test_headless():
    manager = NativeSDRManager()
    devices = manager.discover()
    rtl_devs = [d for d in devices if d.driver == "rtl_sdr"]
    if not rtl_devs:
        print("No RTL-SDR found")
        return
    dev = manager.open(rtl_devs[0].bus)
    app = DummyApp()
    config = StreamConfig(frequency=100_000_000, sample_rate=2_048_000, gain=20.0)
    
    controller = UIController(dev, app, config)
    print("Starting controller")
    controller.start()
    
    print("Waiting 3 seconds...")
    time.sleep(3)
    
    print(f"Total spectrum updates: {app.updates}")
    controller.stop()
    dev.close()

if __name__ == "__main__":
    test_headless()
