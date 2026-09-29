"""
Reusable UI rendering utilities.
"""

import numpy as np


def aggregate_spectrum(
    power: np.ndarray, display_width: int, min_power: float
) -> np.ndarray:
    """
    Downsample a power spectrum array to a given display width using max-pooling.
    This preserves the peaks of narrow signals.
    """
    n_bins = len(power)
    if n_bins == 0 or display_width <= 0:
        return np.full(max(1, display_width), min_power, dtype=np.float32)

    if display_width >= n_bins:
        # If terminal is wider than FFT bins, we could just repeat or pad.
        # But usually we just map up to n_bins, and pad the rest.
        result = np.full(display_width, min_power, dtype=np.float32)
        result[:n_bins] = power
        return result

    # Aggregation size
    chunk_size = max(1, n_bins // display_width)
    downsampled = np.full(display_width, min_power, dtype=np.float32)

    for i in range(display_width):
        start = i * chunk_size
        end = start + chunk_size
        if start < n_bins:
            downsampled[i] = np.max(power[start:end])

    return downsampled


def normalize_power(
    power: np.ndarray, min_power: float, max_power: float
) -> np.ndarray:
    """
    Normalize power (dBFS) to a 0-255 uint8 range for coloring.
    Values outside min_power and max_power are clamped.
    """
    if max_power <= min_power:
        max_power = min_power + 1.0

    # Clip values to bounds
    clipped = np.clip(power, min_power, max_power)

    # Scale to 0.0 - 1.0
    scaled = (clipped - min_power) / (max_power - min_power)

    # Scale to 0 - 255
    return (scaled * 255).astype(np.uint8)
