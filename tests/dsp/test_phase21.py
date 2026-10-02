"""
Phase 21 tests — Multi-channel receiver & signal detection.
"""

import numpy as np

from sdrmon.audio.mixer import AudioMixer
from sdrmon.audio.output import NullAudioOutput
from sdrmon.dsp.channel import Channel, ChannelManager
from sdrmon.dsp.detector import SignalCandidate, SignalDetector, suggest_mode

# ─── ChannelManager multi-channel tests ───────────────────────────────────────


def test_create_channel_returns_channel():
    mgr = ChannelManager(1_000_000, 48000)
    ch = mgr.create_channel(100_000_000, "NFM", 12500.0)
    assert isinstance(ch, Channel)
    assert ch.channel_id == 1
    assert ch.frequency == 100_000_000
    assert ch.mode == "NFM"
    assert ch.bandwidth == 12500.0


def test_create_multiple_channels_unique_ids():
    mgr = ChannelManager(1_000_000, 48000)
    ch1 = mgr.create_channel(100_000_000, "NFM")
    ch2 = mgr.create_channel(100_100_000, "WFM", 200000.0)
    ch3 = mgr.create_channel(99_900_000, "AM")

    assert ch1.channel_id != ch2.channel_id != ch3.channel_id
    assert len(mgr.channels) == 3


def test_remove_channel():
    mgr = ChannelManager(1_000_000, 48000)
    ch = mgr.create_channel(100_000_000, "NFM")
    ch_id = ch.channel_id
    mgr.remove_channel(ch_id)
    assert ch_id not in mgr.channels
    assert len(mgr.channels) == 0


def test_remove_nonexistent_channel_is_safe():
    mgr = ChannelManager(1_000_000, 48000)
    mgr.remove_channel(999)  # Should not raise


def test_enable_disable_channel():
    mgr = ChannelManager(1_000_000, 48000)
    ch = mgr.create_channel(100_000_000, "NFM")
    ch_id = ch.channel_id

    mgr.disable_channel(ch_id)
    assert not mgr.get_channel(ch_id).enabled

    mgr.enable_channel(ch_id)
    assert mgr.get_channel(ch_id).enabled


def test_list_channels():
    mgr = ChannelManager(1_000_000, 48000)
    mgr.create_channel(100_000_000, "NFM")
    mgr.create_channel(100_100_000, "WFM", 200000.0)
    channels = mgr.list_channels()
    assert len(channels) == 2
    assert all(isinstance(c, Channel) for c in channels)


def test_multi_channel_process_produces_n_outputs():
    sdr_rate = 1_000_000
    audio_rate = 48000
    mgr = ChannelManager(sdr_rate, audio_rate)
    mgr.set_sdr_center(100_000_000)

    ch1 = mgr.create_channel(100_000_000, "NFM")
    ch2 = mgr.create_channel(100_100_000, "NFM")
    ch1.squelch = -200.0
    ch2.squelch = -200.0

    iq = np.zeros(1024, dtype=np.complex64)
    outputs = mgr.process(iq)
    assert len(outputs) == 2


def test_disabled_channel_outputs_silence():
    sdr_rate = 1_000_000
    audio_rate = 48000
    mgr = ChannelManager(sdr_rate, audio_rate)
    mgr.set_sdr_center(100_000_000)

    ch = mgr.create_channel(100_000_000, "NFM", 12500.0)
    ch.squelch = -200.0
    ch.enabled = False

    t = np.arange(1024) / sdr_rate
    iq = np.exp(1j * 2 * np.pi * 1000 * t).astype(np.complex64)
    outputs = mgr.process(iq)

    # Disabled channel must output silence (all zeros)
    assert np.all(outputs[0] == 0.0)


def test_muted_channel_outputs_silence():
    sdr_rate = 1_000_000
    audio_rate = 48000
    mgr = ChannelManager(sdr_rate, audio_rate)
    mgr.set_sdr_center(100_000_000)

    ch = mgr.create_channel(100_000_000, "NFM", 12500.0)
    ch.squelch = -200.0
    ch.muted = True

    t = np.arange(1024) / sdr_rate
    iq = np.exp(1j * 2 * np.pi * 1000 * t).astype(np.complex64)
    outputs = mgr.process(iq)

    assert np.all(outputs[0] == 0.0)


def test_set_sdr_rate_preserves_channels():
    mgr = ChannelManager(1_000_000, 48000)
    ch1 = mgr.create_channel(100_000_000, "NFM")
    ch2 = mgr.create_channel(101_000_000, "WFM", 200000.0)
    ch1.squelch = -50.0
    ch2.muted = True

    mgr.set_sdr_rate(2_000_000)

    channels = mgr.list_channels()
    assert len(channels) == 2

    freqs = {c.frequency for c in channels}
    assert 100_000_000 in freqs
    assert 101_000_000 in freqs

    wfm_ch = next(c for c in channels if c.mode == "WFM")
    assert wfm_ch.muted is True


# ─── SignalDetector tests ──────────────────────────────────────────────────────


def make_psd_with_signal(n_bins, center_bin, width_bins, signal_db, noise_db):
    """Create a synthetic PSD with a signal peak."""
    psd = np.full(n_bins, noise_db, dtype=np.float32)
    start = max(0, center_bin - width_bins // 2)
    end = min(n_bins, center_bin + width_bins // 2)
    psd[start:end] = signal_db
    return psd


def test_detector_finds_strong_signal():
    sdr_rate = 1_000_000
    det = SignalDetector(sdr_rate, min_prominence_db=5.0, min_bandwidth=5000.0)

    n_bins = 1024
    psd = make_psd_with_signal(
        n_bins, center_bin=512, width_bins=50, signal_db=-40.0, noise_db=-80.0
    )
    sdr_center = 100_000_000.0

    candidates = det.detect(psd, sdr_center)
    assert len(candidates) >= 1

    # Peak should be near center (100 MHz)
    freqs = [c.frequency for c in candidates]
    assert any(abs(f - sdr_center) < sdr_rate * 0.1 for f in freqs)


def test_detector_returns_empty_on_flat_psd():
    sdr_rate = 1_000_000
    det = SignalDetector(sdr_rate, min_prominence_db=5.0)

    psd = np.full(1024, -80.0, dtype=np.float32)
    candidates = det.detect(psd, 100_000_000.0)
    assert len(candidates) == 0


def test_detector_returns_empty_on_empty_psd():
    det = SignalDetector(1_000_000)
    candidates = det.detect(np.array([]), 100_000_000.0)
    assert candidates == []


def test_detector_noise_floor_estimation():
    sdr_rate = 1_000_000
    det = SignalDetector(sdr_rate, min_prominence_db=5.0)

    psd = make_psd_with_signal(1024, 512, 50, -40.0, -80.0)
    det.detect(psd, 100_000_000.0)
    # Noise floor should be near -80 dB
    assert -90.0 < det.noise_floor_db < -70.0


def test_detector_candidate_has_required_fields():
    det = SignalDetector(1_000_000, min_prominence_db=5.0, min_bandwidth=1000.0)
    psd = make_psd_with_signal(1024, 512, 100, -40.0, -80.0)
    candidates = det.detect(psd, 100_000_000.0)
    assert len(candidates) >= 1
    c = candidates[0]
    assert isinstance(c, SignalCandidate)
    assert c.frequency > 0
    assert c.power > det.noise_floor_db
    assert c.bandwidth > 0
    assert c.confidence > 0
    assert c.timestamp > 0


def test_suggest_mode():
    assert suggest_mode(5000.0) == "NFM"
    assert suggest_mode(12500.0) == "NFM"
    assert suggest_mode(50000.0) == "AM"
    assert suggest_mode(200000.0) == "WFM"


# ─── AudioMixer tests ─────────────────────────────────────────────────────────


def test_mixer_empty_input_is_safe():
    out = NullAudioOutput()
    out.open(None, 48000)
    out.start()
    mixer = AudioMixer(lambda: out)
    mixer.mix_and_write([])  # Should not raise
    assert out.total_samples == 0


def test_mixer_single_channel_passthrough():
    out = NullAudioOutput()
    out.open(None, 48000)
    out.start()
    mixer = AudioMixer(lambda: out)
    audio = np.ones(480, dtype=np.float32) * 0.5
    mixer.mix_and_write([audio])
    assert out.total_samples == 480


def test_mixer_two_channels_sums():
    out = NullAudioOutput()
    out.open(None, 48000)
    out.start()
    mixer = AudioMixer(lambda: out)
    a = np.ones(480, dtype=np.float32) * 0.3
    b = np.ones(480, dtype=np.float32) * 0.2
    mixer.mix_and_write([a, b])
    assert out.total_samples == 480


def test_mixer_prevents_clipping():
    """Peak-limiter should scale down when sum > 1.0."""
    out = NullAudioOutput()
    out.open(None, 48000)
    out.start()

    class CapturingOutput(NullAudioOutput):
        def __init__(self):
            super().__init__()
            self.last = None

        def write(self, samples):
            super().write(samples)
            self.last = samples.copy()

    cap = CapturingOutput()
    cap.open(None, 48000)
    cap.start()
    mixer = AudioMixer(lambda: cap)

    # Two channels both at 0.9 — sum is 1.8, which clips without limiter
    a = np.ones(480, dtype=np.float32) * 0.9
    b = np.ones(480, dtype=np.float32) * 0.9
    mixer.mix_and_write([a, b])

    assert cap.last is not None
    assert np.max(np.abs(cap.last)) <= 1.0 + 1e-4
