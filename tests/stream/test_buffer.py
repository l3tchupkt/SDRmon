"""
Tests for stream buffers and workers.
"""

import numpy as np

from sdrmon.backends.generic.fake import SyntheticStream
from sdrmon.core.samples import IQBlock
from sdrmon.stream.buffer import StreamBuffer, StreamWorker


def test_stream_buffer():
    buf = StreamBuffer(max_blocks=2)
    block1 = IQBlock(np.zeros(10, dtype=np.complex64), 1000, 1000, sequence_number=1)
    block2 = IQBlock(np.zeros(10, dtype=np.complex64), 1000, 1000, sequence_number=2)
    block3 = IQBlock(np.zeros(10, dtype=np.complex64), 1000, 1000, sequence_number=3)

    assert buf.put(block1) is True
    assert buf.put(block2) is True

    # Buffer is full, should fail quickly
    assert buf.put(block3, timeout=0.01) is False

    out1 = buf.get()
    assert out1 is not None
    assert out1.sequence_number == 1

    out2 = buf.get()
    assert out2 is not None
    assert out2.sequence_number == 2

    buf.close()

    # Should get None because of close
    assert buf.get() is None


def test_stream_worker():
    stream = SyntheticStream(
        sample_rate=10_000, center_frequency=100_000, block_size=100
    )
    buf = StreamBuffer(max_blocks=10)

    worker = StreamWorker(stream, buf)
    worker.start()

    # Read a few blocks
    for _ in range(3):
        block = buf.get(timeout=1.0)
        assert block is not None
        assert len(block.samples) == 100

    worker.stop()

    # Drain buffer
    while buf.get(timeout=0.1) is not None:
        pass
