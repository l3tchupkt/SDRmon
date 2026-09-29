# SDRmon

A terminal-first SDR monitoring and analysis toolkit for Python.

Connect an SDR.
Tune a frequency.
Watch the spectrum.
Scan bands.
Capture IQ.
Replay it later.

Everything from the terminal.

## Installation

```bash
pip install sdrmon
```

## Quick Start

```bash
sdrmon
```

## Platform Support

SDRmon's core SDK is designed to run on Windows, Linux, and macOS.

The software-only development workflow requires no SDR hardware:

FakeSDR → DSP → Capture → Replay

Physical SDR support depends on the operating system and vendor/device backend (e.g., RTL-SDR, HackRF, PlutoSDR). You can run `sdrmon platform` to check your environment and available backends.

## Python SDK & Software-Only Workflow

SDRmon is not just a terminal application; it is a powerful Python SDR SDK. You can develop and test SDRmon without owning an physical SDR. The `FakeSDR` device procedurally generates RF signals, and `IQReplay` can loop over saved captures.

```python
from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.settings import StreamConfig
from sdrmon.core.device import DeviceInfo
from sdrmon import SpectrumAnalyzer

device = FakeSDRDevice(DeviceInfo(driver="fake", product="Fake"), seed=42)
device.open()

# Stream 2Msps at 100MHz
config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)

with device.stream(config) as stream:
    block = stream.read()
    
    analyzer = SpectrumAnalyzer(fft_size=2048)
    result = analyzer.process(block)

    print(f"Peak detected at {result.peak_frequency} Hz")
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and architecture details.
