"""
HackRF backend for SDRmon.
"""

from typing import List

from sdrmon.backends.base import SDRBackend
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.settings import StreamConfig
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

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        pass

    def close(self) -> None:
        self.stop()

    def __next__(self) -> IQBlock:
        return self.read()

    def __enter__(self) -> "HackRFStream":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        self.close()


class HackRFDevice(SDRDevice):
    def __init__(self, info: DeviceInfo):
        self._info = info
        self._sdr = None
        self._freq = 0
        self._rate = 0
        self._gain = 0.0

    @property
    def info(self) -> DeviceInfo:
        return self._info

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            frequency=True,
            sample_rate=True,
            gain=True,
            bandwidth=True,
            bias_tee=True,
            transmit=False,
        )

    def open(self) -> None:
        if not HAVE_HACKRF:
            from sdrmon.errors import BackendUnavailableError

            raise BackendUnavailableError(
                "libhackrf is not installed. Install with `pip install sdrmon[hackrf]`."
            )
        # self._sdr = HackRF()

    def close(self) -> None:
        pass

    def set_frequency(self, frequency: int) -> None:
        self._freq = frequency

    def get_frequency(self) -> int:
        return self._freq

    def set_sample_rate(self, sample_rate: int) -> None:
        self._rate = sample_rate

    def get_sample_rate(self) -> int:
        return self._rate

    def set_gain(self, gain: float) -> None:
        self._gain = gain

    def get_gain(self) -> float:
        return self._gain

    def stream(self, config: "StreamConfig | None" = None) -> IQStream:
        return HackRFStream(self._sdr)


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
