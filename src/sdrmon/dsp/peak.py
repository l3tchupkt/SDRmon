"""
Peak detection algorithms.
"""

from typing import Tuple

import numpy as np
from numpy.typing import NDArray


def detect_peak(
    power_db: NDArray[np.float32], freqs: NDArray[np.float64]
) -> Tuple[float, float, float]:
    """
    Detect the strongest peak in the spectrum.
    Returns:
        (peak_frequency, peak_power_db, estimated_bandwidth)
    """
    if len(power_db) == 0:
        return (0.0, -100.0, 0.0)

    peak_idx = np.argmax(power_db)
    peak_power = power_db[peak_idx]
    peak_freq = freqs[peak_idx]

    # Estimate bandwidth: find points where power drops by 3dB from peak
    threshold = peak_power - 3.0

    # search left
    left_idx = peak_idx
    while left_idx > 0 and power_db[left_idx] > threshold:
        left_idx -= 1

    # search right
    right_idx = peak_idx
    while right_idx < len(power_db) - 1 and power_db[right_idx] > threshold:
        right_idx += 1

    bandwidth = freqs[right_idx] - freqs[left_idx]

    return float(peak_freq), float(peak_power), float(bandwidth)
