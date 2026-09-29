# UI Architecture

The SDRmon UI is strictly a consumer of the underlying Python SDR SDK. It is built using the Textual framework.

## Core Rule

> The UI does not implement DSP algorithms, directly access hardware APIs, or manage low-level streams.

## Pipeline

```text
                 Textual TUI
                     │
               UI Controller (Thread)
                     │
             ┌───────┴───────┐
             │               │
          Hardware        Software
             │               │
      RTL/HackRF/Pluto   Fake/Replay
             │               │
             └───────┬───────┘
                     ▼
                  IQStream
                     ▼
              SpectrumAnalyzer
                     ▼
              SpectrumResult
                     │
             UI Message Queue
                     │
          ┌──────────┴──────────┐
          │                     │
    SpectrumWidget        WaterfallWidget
```

## Threading & Streaming

Streaming IQ from SDRs is an intensely blocking, high-throughput operation. If the SDR read loop runs on the main UI thread, Textual's event loop will freeze.

To resolve this, SDRmon uses a `UIController` that manages a background thread.
The thread continuously reads blocks from the `IQStream`, processes them with the `SpectrumAnalyzer`, and uses a latest-frame/backpressure dropping strategy. 

Only a bounded number of `SpectrumUpdated` messages are pushed back to the main Textual app at roughly 30 FPS. This ensures the TUI remains perfectly responsive while the background acquisition happens as fast as the hardware requires.
