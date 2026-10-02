"""
Example: Replaying a captured IQ file
"""

import sys
from pathlib import Path

from sdrmon.replay.replay import IQReplay


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run examples/replay.py <path_to_capture.iq>")
        print("\nIf you don't have a capture, create one with:")
        print("  sdrmon capture --out test.iq --samples 100000")
        return

    capture_file = sys.argv[1]

    if not Path(capture_file).exists():
        print(f"File not found: {capture_file}")
        return

    try:
        # Load the capture file (requires accompanying .json metadata)
        with IQReplay(
            capture_file, block_size=16384, loop=False, rate_control=True
        ) as stream:
            print(f"Replaying {capture_file}...")
            print(
                f"Original Center Frequency: {stream.meta.center_frequency / 1e6:.3f} MHz"
            )
            print(f"Original Sample Rate: {stream.meta.sample_rate / 1e6:.3f} MS/s")

            blocks = 0
            for block in stream:
                blocks += 1
                if blocks % 10 == 0:
                    print(f"Read {blocks} blocks ({stream.position} samples)...")

            print(f"\nReplay finished. Total blocks: {blocks}")

    except Exception as e:
        print(f"Replay failed: {e}")


if __name__ == "__main__":
    main()
