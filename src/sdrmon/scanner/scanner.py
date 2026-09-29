"""
Scanner engine implementation.
"""

import threading
import time
from typing import Iterator

import numpy as np

from sdrmon.analysis.spectrum import SpectrumAnalyzer
from sdrmon.core.device import SDRDevice
from sdrmon.core.settings import StreamConfig
from sdrmon.scanner.errors import ScanConfigurationError
from sdrmon.scanner.models import ScanConfig, ScanResult


class Scanner:
    """RF Scanner Engine."""

    def __init__(self, device: SDRDevice):
        self.device = device
        self._cancel_event = threading.Event()
        self._running = False

    def cancel(self):
        """Cancel an ongoing scan."""
        if self._running:
            self._cancel_event.set()

    def scan(self, config: ScanConfig) -> Iterator[ScanResult]:
        """
        Synchronously scan the configured range, yielding results incrementally.

        This will manage the stream and device frequency tuning internally.
        """
        if self._running:
            raise RuntimeError("A scan is already running.")

        # Validate capabilities
        caps = self.device.capabilities
        if not caps.frequency:
            raise ScanConfigurationError("Device does not support frequency tuning.")
        if not caps.sample_rate:
            raise ScanConfigurationError(
                "Device does not support sample rate configuration."
            )

        self._running = True
        self._cancel_event.clear()

        started_at = time.time()

        analyzer = SpectrumAnalyzer(fft_size=config.fft_size, window="hann")
        stream_config = StreamConfig(
            frequency=config.start_frequency,
            sample_rate=config.sample_rate,
        )

        try:
            # We open the stream once and tune it for each step.
            # Depending on backend, tuning an active stream is well-supported.
            with self.device.stream(stream_config) as stream:
                # Calculate steps deterministically
                span = config.stop_frequency - config.start_frequency
                steps = int(span // config.step)
                # Inclusive stop behavior
                if span % config.step != 0 or steps == 0:
                    steps += 1

                for i in range(steps + 1):
                    if self._cancel_event.is_set():
                        break

                    freq = config.start_frequency + i * config.step
                    if freq > config.stop_frequency:
                        # Allow exactly inclusive but clamp if float math was weird
                        if freq - config.stop_frequency > config.step * 0.01:
                            break
                        freq = config.stop_frequency

                    self.device.set_frequency(freq)

                    if config.settle_time > 0:
                        time.sleep(config.settle_time)

                    if self._cancel_event.is_set():
                        break

                    # Collect samples for dwell_time
                    t_start = time.time()

                    # We will accumulate power across multiple blocks if averaging > 1
                    # Or just process blocks until dwell time expires.
                    # The spec asks for averaging = N to average N spectrums, and dwell time
                    # defines how long we stay. Let's do both: average N blocks within the dwell.

                    blocks = 0
                    linear_power_sum = None
                    last_result = None

                    for block in stream:
                        if self._cancel_event.is_set():
                            break

                        spec_result = analyzer.process(block)
                        last_result = spec_result

                        # Convert dBFS to linear for averaging
                        linear_power = 10 ** (spec_result.power / 10.0)

                        if linear_power_sum is None:
                            linear_power_sum = linear_power
                        else:
                            linear_power_sum += linear_power

                        blocks += 1
                        if (
                            blocks >= config.averaging
                            and (time.time() - t_start) >= config.dwell_time
                        ):
                            break

                    if (
                        last_result is None
                        or linear_power_sum is None
                        or blocks == 0
                        or self._cancel_event.is_set()
                    ):
                        break

                    # Convert back to dBFS
                    avg_linear = linear_power_sum / blocks
                    # protect against log10(0)
                    np.clip(avg_linear, 1e-12, None, out=avg_linear)
                    avg_power = 10.0 * np.log10(avg_linear)

                    peak_idx = int(avg_power.argmax())
                    peak_power = float(avg_power[peak_idx])
                    peak_freq = float(last_result.frequencies[peak_idx])
                    noise_floor = float(np.median(avg_power))

                    # Occupancy logic
                    # Threshold is defined as X dB above estimated noise floor.
                    occupied = peak_power > (noise_floor + config.threshold)

                    scan_result = ScanResult(
                        frequency=freq,
                        peak_frequency=peak_freq,
                        peak_power=peak_power,
                        noise_floor=noise_floor,
                        occupied=occupied,
                        timestamp=time.time(),
                    )

                    yield scan_result

        finally:
            self._running = False
