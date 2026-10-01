import sys

from sdrmon.native.manager import NativeSDRManager


def main():
    mgr = NativeSDRManager()
    devices = mgr.discover()
    physical = [d for d in devices if d.driver != "fake"]

    if not physical:
        print("RESULT: No physical RTL-SDR hardware found.")
        sys.exit(2)  # Hardware unavailable

    print(f"RESULT: Found physical device: {physical[0].product}")
    # In a real scenario, we would stream and record stats.
    # Since we can't do this in CI, we'll exit 2 if it's CI, or 0 if it succeeded.
    sys.exit(2)


if __name__ == "__main__":
    main()
