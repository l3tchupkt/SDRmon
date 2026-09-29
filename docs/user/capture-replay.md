# Capture and Replay

SDRmon provides native support for offline capturing of IQ signals and replaying them accurately using a virtual SDK interface. This helps developers capture anomalous signals in the field with physical hardware and debug their analysis and UI tooling against those signals in a lab setting without real RF hardware attached.

## IQRecorder (Capture)

The `IQRecorder` captures raw IQ `numpy` arrays coming off an `IQStream` into an `.iq` binary file. It seamlessly captures essential metadata simultaneously into an equivalent `.json` file for context-aware replay.

```python
from sdrmon.capture.recorder import IQRecorder

with stream:
    with IQRecorder("capture.iq", device_info=device.info) as recorder:
        for block in stream:
            recorder.write(block)
```

## IQReplay (Replay)

The `IQReplay` acts as a drop-in replacement for any SDK component expecting an `IQStream`. The replay interface fully recovers metadata like timestamp sequence, sample rate, and center frequency from the captured JSON file seamlessly.

```python
from sdrmon.replay.replay import IQReplay

with IQReplay("capture.iq", loop=True, rate_control=False) as replay_stream:
    for block in replay_stream:
        print(f"Replayed sequence {block.sequence_number} at {block.sample_rate} Hz.")
```

### Replay Modes

- **Finite Replay** (`loop=False`): The stream stops and throws `StopIteration` automatically at the end of the file.
- **Looping Replay** (`loop=True`): Re-streams from the start of the file repeatedly upon EOF.
- **Rate-controlled Replay** (`rate_control=True`): Will artificially throttle `read()` times simulating the exact sample rate to closely mimic physical hardware output streams. By default `rate_control=False` for lightning-fast regression testing.
