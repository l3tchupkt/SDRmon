from sdrmon.core.settings import StreamConfig
from sdrmon.native.manager import NativeSDRManager


def run_diagnostics():
    print("Running Native RTL-SDR Diagnostics...")
    manager = NativeSDRManager()

    print("\n[1] Discovery")
    devices = manager.discover()
    rtl_devices = [d for d in devices if d.driver == "rtl_sdr"]

    if not rtl_devices:
        print("FAIL: No RTL-SDR devices found.")
        return

    dev_info = rtl_devices[0]
    print(f"PASS: Found {dev_info.product} (Serial: {dev_info.serial})")

    print("\n[2] Open")
    try:
        dev = manager.open(dev_info.bus)
        print("PASS: Device opened successfully.")
    except Exception as e:
        print(f"FAIL: Could not open device - {e}")
        return

    print("\n[3] Configuration")
    config = StreamConfig(frequency=100_000_000, sample_rate=2_048_000, gain=20.0)

    try:
        # C++ wrapper expects config object
        import sdrmon_native

        nc = sdrmon_native.StreamConfig()
        nc.center_frequency = config.frequency
        nc.sample_rate = config.sample_rate
        nc.gain_mode = sdrmon_native.GainMode.Manual
        nc.gain_value = 20.0

        dev._native.configure(nc)
        print("PASS: Configured to 100 MHz, 2.048 MS/s, 20.0 dB Gain")
    except Exception as e:
        print(f"FAIL: Configuration failed - {e}")
        return

    print("\n[4] Stream Initialization")
    try:
        dev.start()
        stream = dev.stream()
        print("PASS: Stream started, worker thread running.")
    except Exception as e:
        print(f"FAIL: Failed to start stream - {e}")
        return

    print("\n[5] Waiting for First IQ Block")
    try:
        block = stream.next_block()
        if block:
            n = len(block.samples)
            print(f"PASS: Received first IQ block! (Samples: {n})")
            samples = block.samples
            print(
                f"  Sequence: {block.sequence_number}  Rate: {block.sample_rate / 1e6:.3f} MS/s  CF: {block.center_frequency / 1e6:.3f} MHz"
            )
            print(f"  Max I: {samples.real.max():.3f}, Min I: {samples.real.min():.3f}")
            print(f"  Max Q: {samples.imag.max():.3f}, Min Q: {samples.imag.min():.3f}")
            # Check for non-zero (real hardware vs dead silence)
            rms = float((samples.real**2 + samples.imag**2).mean() ** 0.5)
            print(
                f"  RMS amplitude: {rms:.4f} (0.0 = DC / no signal, >0 = data received)"
            )
        else:
            print("FAIL: next_block returned None")
    except Exception as e:
        print(f"FAIL: Error reading block - {e}")

    print("\n[6] Stop and Close")
    try:
        dev.stop()
        dev.close()
        print("PASS: Successfully stopped and closed.")
    except Exception as e:
        print(f"FAIL: Error stopping/closing - {e}")


if __name__ == "__main__":
    run_diagnostics()
