"""
Example: Basic spectrum analysis using SDRmon DSP
"""

import numpy as np

from sdrmon.analysis.spectrum import SpectrumAnalyzer
from sdrmon.core.samples import IQBlock


def main():
    # Create a synthetic signal with a tone at +250 kHz
    sample_rate = 2_000_000
    num_samples = 4096

    t = np.arange(num_samples) / sample_rate
    tone_freq = 250_000

    # Complex sinusoid at +250 kHz + some noise
    samples = np.exp(1j * 2 * np.pi * tone_freq * t).astype(np.complex64)
    samples += (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.1

    block = IQBlock(
        samples=samples.astype(np.complex64),
        sample_rate=sample_rate,
        center_frequency=100_000_000,
        gain=0.0,
        timestamp=0.0,
        sequence_number=0,
    )

    # Analyze
    analyzer = SpectrumAnalyzer(fft_size=2048, window="hann")
    analyzer.process(block)

    # Get the resulting PSD (Power Spectral Density)
    psd = analyzer.get_psd()

    print(f"Computed {len(psd)} point FFT.")

    # Find peak frequency
    max_idx = np.argmax(psd)

    # FFT bins map from -Fs/2 to +Fs/2
    freqs = np.fft.fftshift(np.fft.fftfreq(len(psd), 1.0 / sample_rate))
    peak_freq = freqs[max_idx]

    print(f"Detected peak at {peak_freq / 1000:.1f} kHz relative to center.")
    print(
        f"Absolute peak frequency: {(block.center_frequency + peak_freq) / 1_000_000:.3f} MHz"
    )


if __name__ == "__main__":
    main()
