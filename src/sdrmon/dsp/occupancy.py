"""
Spectrum occupancy estimation.
"""

import numpy as np
from numpy.typing import NDArray


def estimate_occupancy(power_db: NDArray[np.float32], threshold_db: float) -> float:
    """
    Estimate the percentage of the spectrum that is occupied (signal above threshold).
    Returns a value between 0.0 and 1.0.
    """
    if len(power_db) == 0:
        return 0.0

    occupied_bins = np.sum(power_db > threshold_db)
    return float(occupied_bins / len(power_db))
