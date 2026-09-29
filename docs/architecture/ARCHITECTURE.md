# SDRmon Architecture

SDRmon is built around a pluggable backend architecture for SDR hardware, an asynchronous streaming pipeline, and a modular DSP layer.

## Layers

1. **Hardware / Backend Layer**
   - Implements `SDRBackend` and `SDRDevice` interfaces.
   - Converts vendor-specific structures into SDRmon's `IQBlock`.
   
2. **Streaming Layer**
   - Consists of a bounded `StreamBuffer` and a background `StreamWorker`.
   - Prevents memory exhaustion and provides backpressure.
   
3. **DSP Layer**
   - Deterministic and hardware-independent DSP functions (`compute_fft`, `detect_peak`, etc).
   - Can be rigorously tested using synthetic fixtures.
   
4. **UI Layer**
   - Built on Textual.
   - Decoupled from hardware operations, ensuring the event loop remains responsive.
