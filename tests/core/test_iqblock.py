"""
Tests for IQBlock.
"""

import time

import numpy as np

from sdrmon.core.samples import IQBlock


def test_iqblock_creation():
    samples = np.array([1.0 + 1.0j, 2.0 + 2.0j], dtype=np.complex64)
    ts = time.time()

    block = IQBlock(
        samples=samples,
        sample_rate=1000,
        center_frequency=100_000,
        gain=10.0,
        timestamp=ts,
        sequence_number=1,
    )

    assert block.sample_rate == 1000
    assert block.center_frequency == 100_000
    assert block.gain == 10.0
    assert block.timestamp == ts
    assert block.sequence_number == 1
    assert len(block.samples) == 2
    assert block.samples.dtype == np.complex64
    np.testing.assert_array_equal(block.samples, samples)
