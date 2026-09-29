import json

import pytest

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.capture.metadata import CaptureMetadata
from sdrmon.capture.recorder import IQRecorder
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig
from sdrmon.replay.replay import ReplayDevice


@pytest.fixture
def temp_capture_dir(tmp_path):
    return tmp_path


def test_capture_replay_roundtrip(temp_capture_dir):
    iq_path = temp_capture_dir / "test.iq"

    # 1. Start FakeSDR
    info = DeviceInfo("fake", "Fake", "Fake", "1", None, None, None)
    dev = FakeSDRDevice(info, seed=42)
    dev.open()

    # stream config
    freq = 100_000_000
    rate = 2_000_000
    config = StreamConfig(frequency=freq, sample_rate=rate)

    blocks_written = 0
    total_samples = 0

    # 2. Capture data
    with dev.stream(config) as stream:
        with IQRecorder(iq_path, device_info=info) as recorder:
            for i, block in enumerate(stream):
                recorder.write(block)
                blocks_written += 1
                total_samples += len(block.samples)
                if i >= 4:  # record 5 blocks
                    break

    dev.close()

    # 3. Verify files
    json_path = iq_path.with_suffix(".json")
    assert iq_path.exists()
    assert json_path.exists()

    # 4. Verify metadata
    meta = CaptureMetadata.load(json_path)
    assert meta.format == "sdrmon-iq"
    assert meta.version == 1
    assert meta.sample_format == "complex64"
    assert meta.sample_rate == rate
    assert meta.center_frequency == freq
    assert meta.device == "Fake"
    assert meta.samples == total_samples
    assert meta.duration == total_samples / rate

    # Check physical size
    assert iq_path.stat().st_size == total_samples * 8

    # 5. Replay and verify
    meta.validate()

    replay_info = DeviceInfo(
        "replay", "SDRmon", "Replay", str(json_path), "virtual", None, None
    )
    replay_dev = ReplayDevice(replay_info, iq_path, meta)
    replay_dev.open()

    blocks_read = 0
    with replay_dev.stream(None) as r_stream:
        # consume all
        for block in r_stream:
            blocks_read += 1
            assert block.sample_rate == rate
            assert block.center_frequency == freq
            assert len(block.samples) > 0

    replay_dev.close()
    assert blocks_read == blocks_written


def test_capture_metadata_validation(temp_capture_dir):
    json_path = temp_capture_dir / "bad.json"
    bad_data = {
        "format": "wrong",
        "version": 1,
        "sample_format": "complex64",
        "sample_rate": 1000,
        "center_frequency": 1000,
        "gain": None,
        "backend": "fake",
        "device": "Unknown",
        "started_at": "",
        "duration": None,
        "samples": 0,
    }
    with open(json_path, "w") as f:
        json.dump(bad_data, f)

    meta = CaptureMetadata.load(json_path)
    with pytest.raises(ValueError, match="Invalid capture format"):
        meta.validate()
