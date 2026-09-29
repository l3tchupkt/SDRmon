"""
Unit tests for DSP modules.
"""

import numpy as np
import pytest

from sdrmon.dsp.fft import compute_fft, compute_power_spectrum, get_frequencies
from sdrmon.dsp.noise import estimate_noise_floor
from sdrmon.dsp.occupancy import estimate_occupancy
from sdrmon.dsp.peak import detect_peak
from sdrmon.dsp.window import get_window


def generate_tone(freq: float, sample_rate: float, num_samples: int) -> np.ndarray:
    """Generate a complex tone."""
    t = np.arange(num_samples) / sample_rate
    return np.exp(1j * 2 * np.pi * freq * t).astype(np.complex64)


def test_window_generation():
    win = get_window("hann", 1024)
    assert len(win) == 1024
    assert win.dtype == np.float32

    with pytest.raises(ValueError):
        get_window("unknown", 1024)


def test_fft_and_power():
    sample_rate = 2_400_000
    num_samples = 1024
    tone_freq = 100_000  # 100 kHz

    samples = generate_tone(tone_freq, sample_rate, num_samples)

    window = get_window("hann", num_samples)
    fft_data = compute_fft(samples, window)

    window_sum_sq = np.sum(window**2)
    power_db = compute_power_spectrum(fft_data, window_sum_sq)

    freqs = get_frequencies(0, sample_rate, num_samples)

    assert len(power_db) == num_samples
    assert len(freqs) == num_samples

    # Check if the peak is at 100kHz
    peak_idx = np.argmax(power_db)
    assert np.isclose(freqs[peak_idx], tone_freq, atol=sample_rate / num_samples)


def test_peak_detection():
    sample_rate = 1_000_000
    num_samples = 1024
    tone_freq = 250_000

    samples = generate_tone(tone_freq, sample_rate, num_samples)
    window = get_window("blackman-harris", num_samples)
    fft_data = compute_fft(samples, window)
    power_db = compute_power_spectrum(fft_data, np.sum(window**2))
    freqs = get_frequencies(0, sample_rate, num_samples)

    peak_freq, peak_power, bw = detect_peak(power_db, freqs)

    assert np.isclose(peak_freq, tone_freq, atol=sample_rate / num_samples)
    assert peak_power > -20.0  # Tone should be strong
    assert bw > 0


def test_noise_floor():
    # Pure noise
    samples = (np.random.randn(1024) + 1j * np.random.randn(1024)).astype(
        np.complex64
    ) * 0.01
    fft_data = compute_fft(samples)
    power_db = compute_power_spectrum(fft_data)

    noise_floor = estimate_noise_floor(power_db)
    assert noise_floor < 0.0


def test_occupancy():
    power_db = np.array(
        [-100, -90, -80, -20, -10, -20, -80, -90, -100], dtype=np.float32
    )
    occ = estimate_occupancy(power_db, threshold_db=-30.0)
    # 3 out of 9 bins are above -30 (-20, -10, -20)
    assert np.isclose(occ, 3.0 / 9.0)
