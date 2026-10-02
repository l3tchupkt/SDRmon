# SDRmon

A terminal-first SDR monitoring and analysis toolkit for Python. SDRmon provides a full-featured Textual-based UI for exploring RF spectrum directly from your terminal.

## Features
- **Native SDR Backends**: Connect directly to RTL-SDR without needing Python `ctypes` overhead. (Only RTL-SDR is supported natively so far)
- **Real-Time DSP**: Built-in channel manager for FM demodulation and resampling.
- **Spectrum & Waterfall Displays**: Fast terminal graphics rendering.
- **Audio Output**: Demodulate and listen to signals via PortAudio.
- **Scanner**: Automatically scan a frequency range and halt on active signals.
- **Capture & Replay**: Record full IQ bandwidth to disk and replay later precisely as received.
- **Cross-Platform**: Works on Windows, macOS, and Linux terminals.

## Installation

You can install SDRmon directly using `uv` (recommended) or `pip`:

```bash
uv tool install sdrmon
```

To include optional dependencies for TUI, DSP, and Audio:

```bash
uv tool install sdrmon[all]
```

### RTL-SDR Setup (Windows)
SDRmon uses a native C++ extension to talk to RTL-SDR hardware. You need the standard RTL-SDR DLL installed correctly:
1. Download the latest `rtlsdr.dll` and `libusb-1.0.dll` from the RTL-SDR official releases.
2. Place them in your system PATH or in the same directory you run SDRmon.
3. Make sure to use **Zadig** to replace the default USB driver with **WinUSB**. 

## Quick Start

Launch the interactive GUI:

```bash
sdrmon
```

This will open the startup screen where you can select an available SDR device, use a FakeSDR for testing, or replay a capture.

Check device and environment health:

```bash
sdrmon doctor
```

List available SDR devices:

```bash
sdrmon devices
```

Capture 5 seconds of raw IQ data (10M samples at 2MS/s):

```bash
sdrmon capture --out signal.iq --samples 10000000
```

Replay a capture:

```bash
sdrmon replay signal.iq
```

## GUI Controls
Once inside the monitor screen:
- **Frequency/Gain/Rate**: Use the sidebar to tune frequency, change gain, and set sample rate.
- **Demodulation**: The Audio control panel allows setting Mode (WFM/NFM/AM), Squelch, and Volume.
- **Zoom/Scale**: Adjust FFT zooming and DB scaling interactively.
- **Actions**:
  - `SCAN`: Enter Scanner mode.
  - `CAPTURE`: Open the capture dialogue.
  - `REPLAY`: Browse available `.iq` files for replay.
  - `QUIT`: Exit SDRmon.

## Python SDK
You can use the SDRmon components directly in your own scripts. See the `examples/` directory for demonstrations of device usage, spectrum analysis, channel DSP, and PortAudio playback.

```python
from sdrmon.backends import initialize_backends
from sdrmon.native.manager import NativeSDRManager
from sdrmon.core.settings import StreamConfig

initialize_backends()
mgr = NativeSDRManager()
dev = mgr.open("rtlsdr:0")

with dev.stream(StreamConfig(frequency=100_000_000, sample_rate=2_000_000)) as stream:
    for block in stream:
        print(f"Received {len(block.samples)} complex samples!")
```

## Status
- **RTL-SDR physical validation**: NOT PERFORMED (hardware unavailable in CI environment)
- **Synthetic/Replay validation**: PASS

## License
MIT
