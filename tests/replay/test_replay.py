"""
Tests for Replay backend.
"""

from pathlib import Path

import numpy as np

from sdrmon.capture.metadata import CaptureMetadata
from sdrmon.replay.replay import ReplayBackend


def test_replay_backend(tmp_path: Path):
    json_path = tmp_path / "test.json"
    iq_path = tmp_path / "test.iq"

    meta = CaptureMetadata(
        device="fake",
        frequency=100_000,
        sample_rate=10_000,
        gain=0.0,
        format="complex64",
        started_at="2026-09-29T12:00:00Z",
        duration=1.0,
    )
    meta.save(json_path)

    # create some samples
    samples = np.ones(1024, dtype=np.complex64)
    with open(iq_path, "wb") as f:
        f.write(samples.tobytes())

    backend = ReplayBackend()
    backend.add_file(json_path)

    devices = backend.detect()
    assert len(devices) == 1

    dev = backend.open(devices[0])

    assert dev.info.product.startswith("Replay")
    assert not dev.capabilities.frequency

    stream = dev.stream()

    # Read block
    block = next(stream)
    assert block.sample_rate == 10_000
    assert block.center_frequency == 100_000

    # Cleanup
    stream.close()
    dev.close()
