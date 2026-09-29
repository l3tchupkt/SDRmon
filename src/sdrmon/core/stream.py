"""
Base Stream interface.
"""

from abc import ABC, abstractmethod
from typing import Iterator

from sdrmon.core.samples import IQBlock


class IQStream(ABC):
    """Abstract interface for consuming IQ blocks."""

    @abstractmethod
    def read(self) -> IQBlock:
        """Read the next block of IQ samples. Blocks if empty."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the stream."""
        ...

    def __iter__(self) -> Iterator[IQBlock]:
        return self

    @abstractmethod
    def __next__(self) -> IQBlock: ...

    @abstractmethod
    def __enter__(self) -> "IQStream": ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None: ...
