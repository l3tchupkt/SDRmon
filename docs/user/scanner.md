# SDRmon Scanner

SDRmon includes a built-in RF scanner capable of sweeping frequency ranges, measuring peaks, and identifying occupied spectrum based on configurable thresholds.

## CLI Usage

You can run the scanner directly from the CLI without launching the full TUI:

```bash
sdrmon scan --fake --start 100M --stop 110M --step 250k --dwell 0.1
```

### Options

* `--start`: Start frequency (e.g. `100M`)
* `--stop`: Stop frequency (e.g. `110M`)
* `--step`: Step size (e.g. `250k`)
* `--dwell`: Time to dwell on each step in seconds (e.g. `0.1`)
* `--sample-rate`: Sample rate (e.g. `2M`)
* `--fft-size`: FFT resolution (default: 2048)
* `--threshold`: Signal threshold in dB above noise floor (default: 5.0)
* `--averaging`: Number of spectra to average per step (default: 1)
* `--json`: Output stream in JSON format
* `--csv`: Output results to a CSV file

## TUI Usage

In the main SDRmon monitor TUI, press **`S`** to open the Scanner screen.
Currently, this launches a scanner around the active center frequency.

## Output Formats

### Human Readable

```text
Range       100.000 → 110.000 MHz
Step        250.000 kHz
Dwell       100 ms

Scanning...
100.000 MHz   -61.2 dBFS   idle
100.500 MHz   -31.4 dBFS   ACTIVE
```

### JSON

With `--json`, each scan step produces a JSON object to stdout:

```json
{"frequency": 100000000, "peak_frequency": 100000000, "peak_power": -60.1, "noise_floor": -64.0, "occupied": false, "timestamp": 1700000000.123}
```
