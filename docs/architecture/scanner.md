# Scanner Architecture

The Scanner is an independent subsystem built strictly on the SDRmon SDK APIs. It operates without a direct dependency on the Textual TUI, making it usable in scripts, background services, and CLI tools.

## Pipeline

```text
                  Scanner
                     │
          ┌──────────┴──────────┐
          │                     │
      ScanConfig           ScanResults
          │                     │
          ▼                     ▲
       scanner engine
          │
          ▼
      SDRDevice
          │
          ▼
       IQStream
          │
          ▼
  SpectrumAnalyzer
          │
          ▼
  peak / noise / occupancy
```

## Detection Algorithm

At each frequency step:
1. The scanner tunes the `SDRDevice`.
2. A configurable `settle_time` is awaited if needed.
3. IQ blocks are pulled from the `IQStream`.
4. The `SpectrumAnalyzer` processes the blocks into `SpectrumResult` (dBFS).
5. If `averaging > 1`, power values are converted to the linear domain, averaged across multiple blocks, and converted back to dBFS.
6. The noise floor is estimated using the median of the averaged bins.
7. A frequency is marked `occupied = True` if the peak power exceeds `noise_floor + threshold` (in dB).

## Streaming and Concurrency

The Scanner engine (`Scanner.scan()`) is synchronous and yields `ScanResult` via a generator.
- **CLI Mode**: Iterates in the main thread.
- **TUI Mode**: Iterates in a background daemon thread, firing `ScanResultMsg` to the Textual event loop.

## Thread-Safe Cancellation

A `threading.Event()` called `_cancel_event` is checked during tuning and IQ consumption loops. This allows prompt aborts between steps, gracefully closing the active hardware `IQStream` before exiting the generator.
