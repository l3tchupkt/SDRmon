# HackRF Backend

The HackRF backend in SDRmon provides native support for Great Scott Gadgets' HackRF One and compatible hardware. 
It accesses the device directly through the `libhackrf` C library using a custom ctypes wrapper for maximum performance and portability.

## Installation

The HackRF backend is optional. To install SDRmon with HackRF support, you must ensure the native `libhackrf` library is present on your system.

```bash
pip install sdrmon[hackrf]
```

Note: The SDRmon python dependencies for HackRF are minimal, but you **must** install the native library (`libhackrf.so`, `libhackrf.dylib`, or `hackrf.dll`) separately based on your operating system:

- **Windows**: Download the latest release from the official [HackRF GitHub](https://github.com/greatscottgadgets/hackrf) and place `hackrf.dll` in your path, or install via tools like PothosSDR.
- **Linux**: Install via your package manager (e.g., `sudo apt-get install hackrf libhackrf-dev`). You may also need to install the udev rules to allow non-root USB access.
- **macOS**: Install via Homebrew: `brew install hackrf`.

## Features and Limitations

### Receive-Only

The HackRF is a half-duplex transceiver capable of both receiving and transmitting. However, SDRmon is strictly a **receive-only** application. The HackRF backend does not expose any TX capabilities, and safety measures are in place to ensure accidental transmission does not occur.

### Gain Model

The HackRF has three distinct RX gain stages:
1. **LNA (Low Noise Amplifier)**: 0 to 40 dB in 8 dB steps.
2. **VGA (Variable Gain Amplifier)**: 0 to 62 dB in 2 dB steps.
3. **RF Amp**: +14 dB front-end amplifier (disabled by default).

To integrate seamlessly with SDRmon's generic UI, the backend maps a single total gain value (0-102 dB) by intelligently allocating gain across the LNA and VGA stages, prioritizing LNA for an optimal noise figure. The RF Amp is kept disabled for hardware safety and to prevent overdriving the front end.

### Sample Rates and Bandwidth

SDRmon exposes the standard HackRF integer sample rates from 2 MS/s to 20 MS/s. 
The backend automatically configures the hardware baseband filter bandwidth to approximately 75% of the selected sample rate to prevent aliasing.

## Troubleshooting

- **libhackrf unavailable**: Ensure the native library (`libhackrf.so`/`hackrf.dll`) is in your system path.
- **USB permission error (Linux)**: Ensure the HackRF udev rules are installed and your user is in the `plugdev` group.
- **Timeout waiting for samples**: Ensure no other application (like SDR#, GQRX, or another instance of SDRmon) is holding the device open.
