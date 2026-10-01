import sdrmon_native

from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.settings import StreamConfig

from .stream import NativeIQStream


class NativeSDRDevice(SDRDevice):
    """Wrapper for native SDRDevice."""

    def __init__(self, native_device: sdrmon_native.SDRDevice):
        self._native = native_device
        self._stream = None
        self._freq = 0
        self._rate = 0
        self._gain = 0.0

    @property
    def info(self) -> DeviceInfo:
        nd = self._native.info()
        return DeviceInfo(
            driver=nd.backend_name,
            vendor=nd.manufacturer,
            product=nd.product,
            serial=nd.serial,
            bus=None,
            usb_vid=None,
            usb_pid=None,
        )

    @property
    def capabilities(self) -> Capabilities:
        nd_caps = self._native.capabilities()
        return Capabilities(
            frequency=True,
            sample_rate=True,
            gain=nd_caps.has_gain,
            bandwidth=nd_caps.has_bandwidth,
            frequency_correction=nd_caps.has_frequency_correction,
            transmit=nd_caps.has_tx,
            sample_rates=[int(sr[0]) for sr in nd_caps.supported_sample_rates],
            gain_values=nd_caps.supported_gains,
        )

    def open(self) -> None:
        pass # The manager already opened it and returned this device

    def configure(self, config: StreamConfig) -> None:
        native_config = sdrmon_native.StreamConfig()
        native_config.center_frequency = config.frequency
        native_config.sample_rate = config.sample_rate
        if config.bandwidth is not None:
            native_config.bandwidth = config.bandwidth

        if config.gain is not None:
            native_config.gain_mode = sdrmon_native.GainMode.Manual
            native_config.gain_value = float(config.gain)
            self._gain = float(config.gain)
        else:
            native_config.gain_mode = sdrmon_native.GainMode.Automatic

        # Use 16 kS/block (reasonable default for UI update rate)
        native_config.block_size = 16384

        self._native.configure(native_config)
        self._freq = config.frequency
        self._rate = config.sample_rate

    def set_frequency(self, frequency: int) -> None:
        # Records frequency; reconfiguration happens via configure()
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

    def start(self) -> None:
        self._native.start()

    def stop(self) -> None:
        self._native.stop()

    def close(self) -> None:
        self._native.close()

    def stream(self, config: "StreamConfig | None" = None) -> NativeIQStream:
        if config is not None:
            self.configure(config)
        if self._stream is None:
            self._stream = NativeIQStream(self._native.stream())
        return self._stream
