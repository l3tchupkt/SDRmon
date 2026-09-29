"""
FFT and power spectrum functions.
"""

import numpy as np
from numpy.typing import NDArray


def compute_fft(
    samples: NDArray[np.complex64], window: NDArray[np.float32] | None = None
) -> NDArray[np.complex64]:
    """Compute the FFT of complex IQ samples."""
    if window is not None:
        samples = samples * window

    # Compute FFT and shift zero-frequency component to center
    fft_data = np.fft.fft(samples)
    fft_shifted = np.fft.fftshift(fft_data)

    return fft_shifted


def compute_power_spectrum(
    fft_data: NDArray[np.complex64], window_sum_sq: float | None = None
) -> NDArray[np.float32]:
    """
    Compute power spectrum in dBFS from FFT data.
    Takes into account the window coherent gain if window_sum_sq is provided.
    """
    N = len(fft_data)

    # Calculate magnitude squared
    mag_sq = np.abs(fft_data) ** 2

    if window_sum_sq is None:
        window_sum_sq = N

    # Normalize power
    power = mag_sq / (window_sum_sq * N)

    # Avoid log(0)
    power = np.maximum(power, 1e-12)

    # Convert to dB
    power_db = 10 * np.log10(power)

    return power_db.astype(np.float32)


def get_frequencies(
    center_freq: int, sample_rate: int, fft_size: int
) -> NDArray[np.float64]:
    """Get the frequency array corresponding to the FFT bins."""
    return np.fft.fftshift(np.fft.fftfreq(fft_size, d=1.0 / sample_rate)) + center_freq
