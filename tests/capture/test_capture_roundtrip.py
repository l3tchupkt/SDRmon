"""
Tests for Capture and Replay round trip.
"""

from pathlib import Path
import numpy as np

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.capture.recorder import IQRecorder
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig
from sdrmon.replay.replay import IQReplay


def test_capture_replay_roundtrip(tmp_path: Path):
    iq_path = tmp_path / "test.iq"

    info = DeviceInfo(
        driver="fake",
        vendor="Fake",
        product="Fake",
        serial="1",
        bus=None,
        usb_pid=None,
        usb_vid=None,
    )

    dev = FakeSDRDevice(info, seed=123, max_blocks=3)
    dev.open()

    config = StreamConfig(frequency=100_000, sample_rate=10_000)
    stream = dev.stream(config)

    captured_samples = []

    with stream:
        with IQRecorder(iq_path, device_info=info) as recorder:
            for block in stream:
                recorder.write(block)
                captured_samples.append(block.samples)

    dev.close()

    captured_concat = np.concatenate(captured_samples)

    # Replay
    replayed_samples = []

    with IQReplay(iq_path, block_size=8192) as replay:
        for block in replay:
            replayed_samples.append(block.samples)

    replayed_concat = np.concatenate(replayed_samples)

    np.testing.assert_array_equal(captured_concat, replayed_concat)
