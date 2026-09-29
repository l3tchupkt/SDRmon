"""
Models for representing IQ samples and blocks.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class IQBlock:
    """A block of IQ samples with metadata."""

    samples: NDArray[np.complex64]
    sample_rate: int
    center_frequency: int
    gain: float | None = None
    timestamp: float | None = None
    sequence_number: int = 0
