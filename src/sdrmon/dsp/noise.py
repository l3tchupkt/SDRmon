"""
Noise floor estimation.
"""

import numpy as np
from numpy.typing import NDArray


def estimate_noise_floor(
    power_db: NDArray[np.float32], percentile: float = 20.0
) -> float:
    """
    Estimate the noise floor from a power spectrum.
    A simple approach is taking a low percentile of the power bins.
    """
    if len(power_db) == 0:
        return -100.0
    return float(np.percentile(power_db, percentile))
