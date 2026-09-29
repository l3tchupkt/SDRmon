"""
Tests for stream lifecycle.
"""

import pytest

from sdrmon.backends.generic.fake import SyntheticStream


def test_stream_lifecycle():
    stream = SyntheticStream(sample_rate=1000, center_frequency=100_000, max_blocks=2)

    # Read before start
    with pytest.raises(StopIteration):
        stream.read()

    stream.start()

    # Start twice is fine
    stream.start()

    block1 = stream.read()
    assert block1.sequence_number == 0

    block2 = stream.read()
    assert block2.sequence_number == 1

    # Read after max_blocks
    with pytest.raises(StopIteration):
        stream.read()

    stream.stop()

    # Stop twice is fine
    stream.stop()

    stream.close()

    # Close twice is fine
    stream.close()


def test_stream_context_manager():
    with SyntheticStream(
        sample_rate=1000, center_frequency=100_000, max_blocks=1
    ) as stream:
        block = stream.read()
        assert block.sequence_number == 0

    # Read after exit
    with pytest.raises(StopIteration):
        stream.read()
