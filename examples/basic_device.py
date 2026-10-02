"""
Example: Basic SDR Device interaction
"""

import time

from sdrmon.backends import initialize_backends
from sdrmon.core.settings import StreamConfig
from sdrmon.native.manager import NativeSDRManager


def main():
    initialize_backends()
    mgr = NativeSDRManager()
    devices = mgr.discover()

    if not devices:
        print("No SDR devices found.")
        return

    print("Discovered devices:")
    for d in devices:
        print(f" - {d.driver}: {d.product} (serial: {d.serial})")

    dev_info = devices[0]
    if dev_info.driver == "fake":
        print("\nUsing FakeSDR device for demonstration.")

    try:
        dev = mgr.open(dev_info.bus)

        # Access properties
        freq = dev.get_frequency()
        rate = dev.get_sample_rate()

        print(f"Initial Frequency: {freq} Hz")
        print(f"Initial Sample Rate: {rate} Hz")

        # Configure the stream
        config = StreamConfig(frequency=100_000_000, sample_rate=2_000_000)

        print("\nStarting stream...")
        with dev.stream(config) as stream:
            for _ in range(5):
                block = stream.read()
                print(f"Received block: {len(block.samples)} samples")
                time.sleep(0.1)

    except Exception as e:
        print(f"Error communicating with device: {e}")


if __name__ == "__main__":
    main()
