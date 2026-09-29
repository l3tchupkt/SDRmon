"""
Spectrum analysis components.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from sdrmon.core.samples import IQBlock
from sdrmon.dsp.fft import compute_fft, compute_power_spectrum
from sdrmon.dsp.noise import estimate_noise_floor
from sdrmon.dsp.peak import detect_peak


@dataclass(frozen=True)
class SpectrumResult:
    frequencies: NDArray[np.float64]  # Absolute RF frequencies in Hz
    power: NDArray[np.float32]  # Power spectrum in dBFS (relative dB)
    peak_frequency: float | None
    peak_power: float | None
    noise_floor: float | None
    center_frequency: int
    sample_rate: int
    timestamp: float | None

    def __post_init__(self):
        if len(self.frequencies) != len(self.power):
            raise ValueError("frequencies and power arrays must have the same length")
        # Ensure arrays are read-only to guarantee immutability
        self.frequencies.flags.writeable = False
        self.power.flags.writeable = False


class SpectrumAnalyzer:
    """High-level analyzer for processing IQ streams into spectrum data."""

    def __init__(
        self, fft_size: int = 2048, window: str | NDArray[np.float32] | None = "hann"
    ):
        self.fft_size = fft_size
        if isinstance(window, str):
            if window == "hann":
                self.window = np.hanning(fft_size).astype(np.float32)
            elif window == "hamming":
                self.window = np.hamming(fft_size).astype(np.float32)
            elif window == "blackman":
                self.window = np.blackman(fft_size).astype(np.float32)
            else:
                self.window = None
        else:
            self.window = window

        if self.window is not None:
            self.window_sum_sq = float(np.sum(self.window) ** 2 / self.fft_size)
        else:
            self.window_sum_sq = None

    def process(self, block: IQBlock) -> SpectrumResult:
        """Process an IQ block and return the spectrum result."""
        # Trim or pad samples to fit fft_size if necessary
        samples = block.samples
        if len(samples) >= self.fft_size:
            samples = samples[: self.fft_size]
        else:
            padded = np.zeros(self.fft_size, dtype=np.complex64)
            padded[: len(samples)] = samples
            samples = padded

        # Compute FFT and power spectrum
        fft_data = compute_fft(samples, self.window)
        power_spectrum = compute_power_spectrum(fft_data, self.window_sum_sq)

        # Compute frequencies
        freqs = np.fft.fftfreq(self.fft_size, d=1.0 / block.sample_rate)
        freqs = np.fft.fftshift(freqs) + block.center_frequency

        # Find peak
        peak_frequency, peak_power, _ = detect_peak(power_spectrum, freqs)

        # Estimate noise floor
        noise_floor = float(estimate_noise_floor(power_spectrum))

        return SpectrumResult(
            frequencies=freqs.astype(np.float64),
            power=power_spectrum.astype(np.float32),
            peak_frequency=peak_frequency,
            peak_power=peak_power,
            noise_floor=noise_floor,
            center_frequency=block.center_frequency,
            sample_rate=block.sample_rate,
            timestamp=block.timestamp,
        )
