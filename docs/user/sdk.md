# SDRmon SDK

SDRmon provides a powerful Python SDK for software-defined radio development, testing, and offline analysis. You can use this SDK to interface with hardware like RTL-SDR, HackRF, and PlutoSDR, or use the integrated Fake and Replay backends.

## Example

Here is a minimal script that uses the FakeSDR for development, streams data, and performs spectrum analysis:

```python
from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig
from sdrmon import SpectrumAnalyzer

# Setup a fake device with a deterministic seed
info = DeviceInfo(
    driver="fake",
    vendor="Fake",
    product="Fake",
    serial="1",
    bus=None,
    usb_pid=None,
    usb_vid=None,
)
device = FakeSDRDevice(info, seed=42)
device.open()

config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)

with device.stream(config) as stream:
    # Read a block of IQ samples
    block = next(stream)

    # Analyze the spectrum
    analyzer = SpectrumAnalyzer(fft_size=2048)
    result = analyzer.process(block)

    print(f"Peak detected at: {result.peak_frequency} Hz")

device.close()
```

## Software-Only Workflow

You do not need an actual SDR hardware to develop, test, or analyze data with SDRmon! The `FakeSDRDevice` generates synthetic but realistic IQ signals, while the `IQReplay` and `IQRecorder` components allow you to capture signals on a real device, save them to disk, and replay them seamlessly using the identical pipeline on another machine.
