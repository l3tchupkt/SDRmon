"""
Tests for Fake SDR Device.
"""

from sdrmon.backends.generic.fake import FakeSDRDevice
from sdrmon.core.device import DeviceInfo
from sdrmon.core.settings import StreamConfig


def test_fake_device_determinism():
    info = DeviceInfo(
        driver="fake",
        vendor="Fake",
        product="Fake",
        serial="1",
        bus=None,
        usb_pid=None,
        usb_vid=None,
    )

    dev1 = FakeSDRDevice(info, seed=42)
    dev1.open()
    stream1 = dev1.stream(StreamConfig(frequency=100_000, sample_rate=1000))
    stream1.start()
    block1 = stream1.read()
    dev1.close()

    dev2 = FakeSDRDevice(info, seed=42)
    dev2.open()
    stream2 = dev2.stream(StreamConfig(frequency=100_000, sample_rate=1000))
    stream2.start()
    block2 = stream2.read()
    dev2.close()

    import numpy as np

    np.testing.assert_array_equal(block1.samples, block2.samples)


def test_fake_device_different_seed():
    info = DeviceInfo(
        driver="fake",
        vendor="Fake",
        product="Fake",
        serial="1",
        bus=None,
        usb_pid=None,
        usb_vid=None,
    )

    dev1 = FakeSDRDevice(info, seed=42)
    dev1.open()
    stream1 = dev1.stream(StreamConfig(frequency=100_000, sample_rate=1000))
    stream1.start()
    block1 = stream1.read()
    dev1.close()

    dev2 = FakeSDRDevice(info, seed=43)
    dev2.open()
    stream2 = dev2.stream(StreamConfig(frequency=100_000, sample_rate=1000))
    stream2.start()
    block2 = stream2.read()
    dev2.close()

    import numpy as np

    assert not np.array_equal(block1.samples, block2.samples)
