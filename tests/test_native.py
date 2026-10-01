import threading
import time

import sdrmon_native

from sdrmon.native.manager import NativeSDRManager


def test_native_manager_discovery():
    manager = NativeSDRManager()
    devices = manager.discover()
    assert len(devices) > 0

    fake_found = False
    for dev in devices:
        if dev.device_id.startswith("FakeSDR"):
            fake_found = True
            assert dev.driver == "FakeSDR"
    assert fake_found


def test_native_fake_stream():
    manager = NativeSDRManager()
    dev = manager.open("fake:0")

    nc = sdrmon_native.StreamConfig()
    nc.center_frequency = 100_000_000
    nc.sample_rate = 1_000_000
    nc.block_size = 16384
    dev._native.configure(nc)

    dev.start()
    stream = dev.stream()
    assert stream.running()

    # Read a block
    block = stream.next_block()
    assert block is not None

    dev.stop()
    assert not stream.running()


def test_native_gil_release():
    manager = NativeSDRManager()
    dev = manager.open("fake:0")
    nc = sdrmon_native.StreamConfig()
    nc.center_frequency = 100_000_000
    nc.sample_rate = 1_000_000
    nc.block_size = 163840
    dev._native.configure(nc)

    dev.start()
    stream = dev.stream()

    # Run a python background thread that just spins
    spin_count = 0
    keep_spinning = True

    def spinner():
        nonlocal spin_count
        while keep_spinning:
            spin_count += 1
            time.sleep(0.001)

    t = threading.Thread(target=spinner)
    t.start()

    # This should block in C++ without holding the GIL
    block = stream.next_block()

    keep_spinning = False
    t.join()

    assert block is not None
    # If the GIL was released, the spinner thread should have executed many times
    assert spin_count > 0

    dev.stop()
