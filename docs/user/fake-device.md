# FakeSDR Device

SDRmon includes a `FakeSDRDevice` which provides a deterministic, software-only SDR implementation designed specifically for development and testing.

## Overview

The `FakeSDRDevice` does not interact with any hardware. Instead, it procedurally generates IQ signals in memory. It uses the exact same `SDRDevice`, `IQStream`, and `IQBlock` semantics as hardware drivers, guaranteeing that UI or DSP logic developed against `FakeSDRDevice` will work seamlessly on real hardware like HackRF or RTL-SDR.

## Key Features

- **Deterministic Output**: Uses a configurable PRNG seed (`seed=42`) to guarantee identical output sequences across test runs, crucial for DSP algorithm regression testing.
- **Configurable Signals**: Generates an IQ stream composed of a complex sinusoid (e.g., 100 kHz tone) over a baseline Gaussian noise floor. 
- **Finite Streaming Mode**: Provides `max_blocks` which limits the stream size, useful for test suite automation to prevent hanging indefinitely.

## Example Usage

```python
from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig

# A Fake SDR Device requires minimal device info
info = DeviceInfo(
    driver="fake",
    vendor="Fake",
    product="Fake",
    serial="1",
    bus=None,
    usb_pid=None,
    usb_vid=None,
)

# Initialize with deterministic seed
device = FakeSDRDevice(info, seed=123)
device.open()

# Stream configuration (Sample rate and center frequency are supported)
config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)

with device.stream(config) as stream:
    block = next(stream)
    print(block.samples)

device.close()
```
