"""
Example: Direct Audio Output
"""

import time

import numpy as np

try:
    from sdrmon.audio.output import SoundDeviceAudioOutput
except ImportError:
    SoundDeviceAudioOutput = None


def main():
    if SoundDeviceAudioOutput is None:
        print("Error: sounddevice is not installed. Run `pip install sdrmon[audio]`")
        return

    print("Initializing Audio Output (48 kHz)...")
    out = SoundDeviceAudioOutput(sample_rate=48000)
    out.start()

    # Generate a 440Hz beep
    sample_rate = 48000
    duration = 2.0
    t = np.arange(int(sample_rate * duration)) / sample_rate
    beep = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

    # Break into chunks to simulate continuous streaming
    chunk_size = 1024
    print("Playing 440 Hz tone for 2 seconds...")

    try:
        for i in range(0, len(beep), chunk_size):
            chunk = beep[i : i + chunk_size]
            out.write(chunk)
            # Sleep slightly less than chunk duration to keep buffer full
            time.sleep((chunk_size / sample_rate) * 0.9)

        print("Finished pushing audio.")
        # Wait a moment for queue to drain
        time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        out.stop()
        stats = out.get_stats()
        print("\nAudio Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
