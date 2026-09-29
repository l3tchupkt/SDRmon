"""
Stream buffer and worker pipeline.
"""

import logging
import queue
import threading
from typing import Optional

from sdrmon.core.samples import IQBlock
from sdrmon.core.stream import IQStream

logger = logging.getLogger(__name__)


class StreamBuffer:
    """A bounded buffer for IQ streams with backpressure."""

    def __init__(self, max_blocks: int = 100):
        self._queue: queue.Queue[Optional[IQBlock]] = queue.Queue(maxsize=max_blocks)

    def put(self, block: IQBlock, timeout: float = 1.0) -> bool:
        """Put a block into the buffer. Returns True on success, False if full."""
        try:
            self._queue.put(block, timeout=timeout)
            return True
        except queue.Full:
            return False

    def get(self, timeout: float = 1.0) -> Optional[IQBlock]:
        """Get a block from the buffer. Returns None on timeout or EOF."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        """Signal EOF."""
        try:
            self._queue.put(None, timeout=1.0)
        except queue.Full:
            pass


class StreamWorker:
    """Reads from an SDR stream in a background thread and pushes to a buffer."""

    def __init__(self, stream: IQStream, buffer: StreamBuffer):
        self.stream = stream
        self.buffer = buffer
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.stream.stop()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.buffer.close()

    def _run(self) -> None:
        try:
            for block in self.stream:
                if self._stop_event.is_set():
                    break

                # Backpressure handled by StreamBuffer's put timeout
                success = self.buffer.put(block, timeout=0.1)
                if not success:
                    # Dropping block to prevent unbounded memory
                    logger.warning(
                        "Stream buffer full, dropping block %d", block.sequence_number
                    )

        except Exception as e:
            logger.error(f"Stream worker error: {e}")
        finally:
            self.buffer.close()
