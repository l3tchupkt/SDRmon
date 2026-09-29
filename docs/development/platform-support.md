# Platform Support

SDRmon's core SDK is designed to be fully platform-independent and runs seamlessly on Windows, Linux, and macOS. 

## Fully Portable (No Hardware Required)

The following components are guaranteed to work on any OS supporting Python 3.10+:

* **Core SDK**: Streams, buffers, and block management
* **FakeSDR**: Deterministic synthetic IQ signal generation
* **Replay**: File-based loop/finite streaming of `.iq` files
* **Capture**: Capturing streams natively to disk
* **DSP / Analysis**: `SpectrumAnalyzer` and FFT computations
* **CLI**: Argument parsing and software workflows

## Hardware/Environment Dependent

Physical SDR support natively relies on hardware drivers and optional C-libraries installed on the host system:

* **RTL-SDR**: Requires `librtlsdr` on the system and installing `sdrmon[rtlsdr]`.
* **HackRF**: Requires `libhackrf` on the system and installing `sdrmon[hackrf]`.
* **PlutoSDR**: Requires `libiio` and installing `sdrmon[pluto]`.

If a backend's dependencies are missing, the core SDK continues to work normally. Requesting a missing backend will raise a `BackendUnavailableError` instructing the user how to install the required dependency.
