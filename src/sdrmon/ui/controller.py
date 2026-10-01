"""
UI Controller for background stream processing.
"""

import threading
import time
from typing import Optional

from sdrmon.analysis.spectrum import SpectrumAnalyzer
from sdrmon.capture.recorder import IQRecorder
from sdrmon.core.device import SDRDevice
from sdrmon.core.settings import StreamConfig
from sdrmon.core.stream import IQStream

from textual.message import Message


class StreamErrorMsg(Message):
    """Sent when an error occurs in the background stream worker."""

    def __init__(self, err: Exception):
        super().__init__()
        self.error = err


class UIController:
    """Manages the background thread for acquiring IQ and emitting UI events."""

    def __init__(
        self,
        device: SDRDevice,
        app,
        config: StreamConfig,
        fft_size: int = 2048,
        window: str = "hann",
    ):
        self.device = device
        self.app = app
        self.config = config
        self.fft_size = fft_size
        self.window = window

        self._stream: Optional[IQStream] = None
        self._analyzer: Optional[SpectrumAnalyzer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False
        self._stop_event = threading.Event()
        self.recorder: Optional[IQRecorder] = None

    def start(self):
        """Start the background worker."""
        if self._running:
            return

        self._analyzer = SpectrumAnalyzer(fft_size=self.fft_size, window=self.window)
        self._stream = self.device.stream(self.config)
        self._stream.start()

        self._running = True
        self._paused = False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background worker."""
        self._running = False
        self._stop_event.set()

        if self._stream:
            self._stream.close()

        if self._thread:
            # We don't join to avoid blocking the UI thread.
            # The daemon thread will exit once _stop_event is set and stream closes.
            self._thread = None

        self._stream = None

    def pause(self):
        """Pause UI updates (keeps streaming under the hood)."""
        self._paused = True

    def resume(self):
        """Resume UI updates."""
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    def set_frequency(self, freq: int):
        self.device.set_frequency(freq)

    def set_gain(self, gain: float):
        self.device.set_gain(gain)

    def set_sample_rate(self, rate: int):
        self.device.set_sample_rate(rate)
        # Update config to keep in sync
        self.config = StreamConfig(
            frequency=self.device.get_frequency(),
            sample_rate=rate,
            gain=self.config.gain,
        )
        # Restart stream if needed, for many SDK devices set_sample_rate immediately takes effect

    def set_window(self, window: str):
        self.window = window
        self._analyzer = SpectrumAnalyzer(fft_size=self.fft_size, window=self.window)

    def _worker(self):
        """Background thread loop."""
        from sdrmon.ui.widgets.spectrum import SpectrumUpdated

        # Throttle UI updates to max 30 FPS
        min_interval = 1.0 / 30.0
        last_update = 0.0

        try:
            if self._stream:
                for block in self._stream:
                    if self._stop_event.is_set():
                        break

                    if self._paused:
                        # Keep consuming to avoid buffer bloat, but skip processing
                        continue

                    if self.recorder:
                        try:
                            self.recorder.write(block)
                        except Exception as e:
                            # Pass error back and stop recording
                            from sdrmon.ui.screens.capture import CaptureErrorMsg

                            self.app.post_message(CaptureErrorMsg(e))
                            self.recorder.close()
                            self.recorder = None

                    now = time.monotonic()
                    if now - last_update >= min_interval:
                        if self._analyzer:
                            result = self._analyzer.process(block)
                            # Push to Textual UI thread
                            self.app.post_message(SpectrumUpdated(result))
                        last_update = now

        except Exception as e:
            # Use post_message to send error state to UI
            self.app.post_message(StreamErrorMsg(e))
        finally:
            self._running = False
