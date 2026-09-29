# Terminal UI (TUI)

SDRmon includes a powerful Terminal UI built on Textual. It gives you a complete Spectrum Analyzer experience right in your terminal.

## Launching the TUI

To start the TUI using your connected SDR:

```bash
sdrmon monitor
```

## FakeSDR Mode (No Hardware Required)

You can run the TUI without physical hardware. The FakeSDR backend generates a procedural RF signal with a sliding peak, making it perfect for development and demonstration:

```bash
sdrmon monitor --fake
```

## Keyboard Controls

| Key     | Action |
|---------|--------|
| `q`     | Quit the application safely |
| `Space` | Pause / Resume spectrum updates |
| `w`     | Cycle FFT window function (Hann, Hamming, Blackman, Rectangular) |

## Supported Settings

The status panel displays the current hardware state:
* **Frequency:** Center frequency of the tuner.
* **Sample Rate:** IQ sampling rate.
* **Gain:** Baseband / LNA gain.
* **FFT Size:** Resolution of the spectrum analysis.
* **Window:** Signal window applied before FFT.

*(Note: In Phase 5, Frequency, Gain, Sample rate, and Zoom controls are mapped but not yet fully interactive via modal dialogs).*

## Terminal Sizing

The TUI uses automatic resampling to map the high-resolution FFT (e.g. 2048 bins) down to your terminal's character width while preserving peaks. You can resize your terminal at any time and the spectrum will gracefully adapt.
