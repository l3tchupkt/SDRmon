"""
HackRF backend for SDRmon.
"""

from typing import List

from sdrmon.backends.base import SDRBackend
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.stream import IQStream

try:
    import libhackrf  # noqa: F401  # type: ignore

    HAVE_HACKRF = True
except ImportError:
    HAVE_HACKRF = False


from typing import Any


class HackRFStream(IQStream):
    # Minimal mock since we can't fully test
    def __init__(self, sdr: Any):
        self.sdr = sdr
        self._running = False

    def read(self) -> IQBlock:
        raise NotImplementedError()

    def stop(self) -> None:
        pass

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "HackRFStream":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.stop()


class HackRFDevice(SDRDevice):
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
            bias_tee=True,
            transmit=False,
        )

    def open(self) -> None:
        if not HAVE_HACKRF:
            raise RuntimeError("libhackrf is not installed.")
        # self._sdr = HackRF()

    def close(self) -> None:
        pass

    def set_frequency(self, frequency: int) -> None:
        pass

    def set_sample_rate(self, sample_rate: int) -> None:
        pass

    def set_gain(self, gain: float) -> None:
        pass

    def start_stream(self) -> IQStream:
        return HackRFStream(self._sdr)

    def stop_stream(self) -> None:
        pass


class HackRFBackend(SDRBackend):
    @property
    def name(self) -> str:
        return "hackrf"

    def detect(self) -> List[DeviceInfo]:
        if not HAVE_HACKRF:
            return []
        return []

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        dev = HackRFDevice(device_info)
        dev.open()
        return dev
