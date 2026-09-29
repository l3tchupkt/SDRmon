"""
PlutoSDR backend for SDRmon.
"""

from typing import List

from sdrmon.backends.base import SDRBackend
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.stream import IQStream

try:
    import adi  # noqa: F401  # type: ignore

    HAVE_PLUTO = True
except ImportError:
    HAVE_PLUTO = False


from typing import Any


class PlutoStream(IQStream):
    # Minimal mock
    def __init__(self, sdr: Any):
        self.sdr = sdr
        self._running = False

    def read(self) -> IQBlock:
        raise NotImplementedError()

    def stop(self) -> None:
        pass

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "PlutoStream":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.stop()


class PlutoDevice(SDRDevice):
    def __init__(self, info: DeviceInfo):
        self._info = info
        self._sdr = None

    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency_tuning=True,
            sample_rate=True,
            gain_control=True,
            bandwidth_control=True,
            transmit=False,
        )

    def open(self) -> None:
        if not HAVE_PLUTO:
            raise RuntimeError("adi library is not installed.")
        # self._sdr = adi.Pluto(self._info.serial)

    def close(self) -> None:
        pass

    def set_frequency(self, frequency: int) -> None:
        pass

    def set_sample_rate(self, sample_rate: int) -> None:
        pass

    def set_gain(self, gain: float) -> None:
        pass

    def start_stream(self) -> IQStream:
        return PlutoStream(self._sdr)

    def stop_stream(self) -> None:
        pass


class PlutoSDRBackend(SDRBackend):
    @property
    def name(self) -> str:
        return "pluto"

    def detect(self) -> List[DeviceInfo]:
        if not HAVE_PLUTO:
            return []
        return []

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        dev = PlutoDevice(device_info)
        dev.open()
        return dev
