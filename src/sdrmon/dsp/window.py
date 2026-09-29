"""
Window functions for DSP.
"""

import numpy as np
from numpy.typing import NDArray


def get_window(name: str, size: int) -> NDArray[np.float32]:
    """
    Get a window function by name.
    Supported: hann, hamming, blackman, blackman-harris, rectangular
    """
    name = name.lower()
    if name == "hann":
        return np.hanning(size).astype(np.float32)
    elif name == "hamming":
        return np.hamming(size).astype(np.float32)
    elif name == "blackman":
        return np.blackman(size).astype(np.float32)
    elif name in ("blackman-harris", "blackmanharris"):
        # standard blackman-harris constants
        a0 = 0.35875
        a1 = 0.48829
        a2 = 0.14128
        a3 = 0.01168
        n = np.arange(size)
        N = size
        w = (
            a0
            - a1 * np.cos(2 * np.pi * n / N)
            + a2 * np.cos(4 * np.pi * n / N)
            - a3 * np.cos(6 * np.pi * n / N)
        )
        return w.astype(np.float32)
    elif name == "rectangular":
        return np.ones(size, dtype=np.float32)
    else:
        raise ValueError(f"Unknown window type: {name}")
