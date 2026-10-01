from typing import Optional

import sdrmon_native

from sdrmon.core.samples import IQBlock
from sdrmon.core.stream import IQStream


class NativeIQStream(IQStream):
    """Wrapper for native IQStream."""

    def __init__(self, native_stream: sdrmon_native.IQStream):
        self._native = native_stream

    def start(self) -> None:
        self._native.start()

    def stop(self) -> None:
        self._native.stop()

    def running(self) -> bool:
        return self._native.running()

    def next_block(self) -> Optional[IQBlock]:
        nb = self._native.next_block()
        if nb is None:
            return None
        return IQBlock(
            samples=nb.data,
            sample_rate=int(nb.sample_rate),
            center_frequency=int(nb.center_frequency),
            timestamp=nb.timestamp,
            sequence_number=nb.sequence_number,
        )

    def try_next_block(self) -> Optional[IQBlock]:
        nb = self._native.try_next_block()
        if nb is None:
            return None
        return IQBlock(
            samples=nb.data,
            sample_rate=int(nb.sample_rate),
            center_frequency=int(nb.center_frequency),
            timestamp=nb.timestamp,
            sequence_number=nb.sequence_number,
        )

    def available(self) -> int:
        return self._native.available()

    def read(self) -> IQBlock:
        block = self.next_block()
        if block is None:
            raise StopIteration
        return block

    def close(self) -> None:
        self.stop()

    def __enter__(self) -> "NativeIQStream":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __next__(self) -> IQBlock:
        return self.read()
