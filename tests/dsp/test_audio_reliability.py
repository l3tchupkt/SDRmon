import queue

import numpy as np

from sdrmon.audio.output import AudioOutput
from sdrmon.dsp.channel import ChannelManager
from sdrmon.dsp.filters import Resampler


class MockAudioOutput(AudioOutput):
    def __init__(self):
        self.q = queue.Queue(maxsize=100)
        self.underruns = 0
        self.overruns = 0
        self.generated = 0
        self.dropped = 0

    def discover(self):
        return []

    def open(self, device, rate):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        pass

    def write(self, samples):
        self.generated += len(samples)
        try:
            if self.q.full():
                try:
                    self.q.get_nowait()
                    self.dropped += len(samples)
                    self.overruns += 1
                except queue.Empty:
                    pass
            self.q.put_nowait(samples)
        except queue.Full:
            self.dropped += len(samples)
            self.overruns += 1

    def get_stats(self):
        return {
            "underruns": self.underruns,
            "overruns": self.overruns,
            "generated": self.generated,
            "dropped": self.dropped,
        }


def test_dsp_continuity():
    sdr_rate = 1_000_000
    audio_rate = 48000
    mgr_single = ChannelManager(sdr_rate, audio_rate)
    mgr_split = ChannelManager(sdr_rate, audio_rate)

    ch_single = mgr_single.create_channel(100_000_000, "WFM", 200000.0)
    ch_single.squelch = -200

    ch_split = mgr_split.create_channel(100_000_000, "WFM", 200000.0)
    ch_split.squelch = -200

    # Generate a dummy complex sine wave signal
    t = np.arange(int(sdr_rate * 0.1)) / sdr_rate
    iq = np.exp(1j * 2 * np.pi * 1000 * t).astype(np.complex64)

    # Process all at once
    audio_single = mgr_single.process(iq)[0]

    # Process in 10 chunks
    chunks = np.array_split(iq, 10)
    audio_split = []
    for chunk in chunks:
        audio_split.append(mgr_split.process(chunk)[0])
    audio_split = np.concatenate(audio_split)

    # Check that lengths are almost equal (due to upfirdn buffering there might be tiny differences)
    assert abs(len(audio_single) - len(audio_split)) < 10

    # Check that values are very close
    min_len = min(len(audio_single), len(audio_split))
    np.testing.assert_allclose(audio_single[:min_len], audio_split[:min_len], atol=1e-3)


def test_audio_queue_overflow():
    audio = MockAudioOutput()
    audio.q = queue.Queue(maxsize=2)  # Very small queue

    # Simulate writing 5 chunks
    for _ in range(5):
        audio.write(np.zeros(1024, dtype=np.float32))

    stats = audio.get_stats()
    assert stats["generated"] == 5 * 1024
    assert stats["overruns"] > 0
    assert stats["dropped"] > 0
    assert audio.q.qsize() == 2  # Remains bounded


def test_resampler_bounds():
    resampler = Resampler(2048000, 48000)
    iq = np.zeros(2048, dtype=np.float32)
    # output should be around 48 samples
    out = resampler.process(iq)
    assert 40 <= len(out) <= 55
