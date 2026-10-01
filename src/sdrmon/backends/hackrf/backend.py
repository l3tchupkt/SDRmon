import ctypes
import queue
import time
from typing import Any, List, Optional

import numpy as np

from sdrmon.backends.base import SDRBackend
from sdrmon.core.capabilities import Capabilities
from sdrmon.core.device import DeviceInfo, SDRDevice
from sdrmon.core.samples import IQBlock
from sdrmon.core.settings import StreamConfig
from sdrmon.core.stream import IQStream
from sdrmon.errors import BackendError, BackendUnavailableError

from .libhackrf import (
    HACKRF_ERROR_OK,
    hackrf_transfer,
    libhackrf,
)


class HackRFStream(IQStream):
    def __init__(self, sdr: "HackRFDevice", config: StreamConfig):
        self.sdr = sdr
        self.config = config
        self._queue: queue.Queue[IQBlock] = queue.Queue(maxsize=16)
        self._running = False
        self._seq = 0
        self._callback = self._rx_callback

        # Keep a reference to the CFUNCTYPE to prevent garbage collection
        self._c_callback = ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.POINTER(hackrf_transfer)
        )(self._callback)

    def _rx_callback(self, transfer_ptr: Any) -> int:
        if not self._running:
            return 0

        transfer = transfer_ptr.contents
        valid_len = transfer.valid_length

        if valid_len > 0:
            # HackRF provides 8-bit signed IQ samples interleaved (I, Q, I, Q...)
            # The buffer is a ctypes POINTER(c_byte). We cast it to a numpy array.
            # We copy it out immediately so the callback can return.
            # ctypes.string_at creates a bytes object, from which we make a numpy array.
            buffer_bytes = ctypes.string_at(transfer.buffer, valid_len)

            # Convert to signed 8-bit ints, then to complex64
            # Format: [I0, Q0, I1, Q1, ...]
            raw = np.frombuffer(buffer_bytes, dtype=np.int8).astype(np.float32)

            # Normalize from [-128, 127] to [-1.0, 1.0]
            raw /= 128.0

            samples = raw[0::2] + 1j * raw[1::2]

            block = IQBlock(
                samples=samples.astype(np.complex64),
                sample_rate=self.config.sample_rate,
                center_frequency=self.config.frequency,
                gain=self.config.gain if self.config.gain is not None else 0.0,
                timestamp=time.time(),
                sequence_number=self._seq,
            )
            self._seq += 1

            try:
                self._queue.put_nowait(block)
            except queue.Full:
                # Backpressure: drop block if consumer is too slow
                pass

        return 0

    def start(self) -> None:
        assert libhackrf is not None
        if not self._running:
            self._running = True
            # Empty queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

            res = libhackrf.hackrf_start_rx(self.sdr._dev, self._c_callback, None)
            if res != HACKRF_ERROR_OK:
                self._running = False
                raise BackendError(f"Failed to start RX: {res}")

    def read(self, timeout: float = 1.0) -> IQBlock:
        if not self._running:
            raise StopIteration()
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            if not self._running:
                raise StopIteration()
            raise TimeoutError("Timeout waiting for HackRF samples")

    def stop(self) -> None:
        assert libhackrf is not None
        if self._running:
            self._running = False
            # Signal HackRF to stop RX
            libhackrf.hackrf_stop_rx(self.sdr._dev)

            # Unblock any pending read
            try:
                self._queue.put_nowait(None)  # type: ignore
            except queue.Full:
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
        exc_type: type[BaseException] | Optional[BaseException],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        self.close()


class HackRFDevice(SDRDevice):
    def __init__(self, info: DeviceInfo):
        self._info = info
        self._dev = None
        self._freq = 100_000_000
        self._rate = 2_000_000
        self._gain = 0.0
        self._amp = False

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
            bias_tee=False,  # We map Amp as a separate concern, or keep bias tee false
            transmit=False,
            # Common HackRF rates
            sample_rates=[
                2_000_000,
                4_000_000,
                8_000_000,
                10_000_000,
                12_500_000,
                16_000_000,
                20_000_000,
            ],
            # Total gain: LNA (0..40, step 8) + VGA (0..62, step 2)
            gain_values=[float(x) for x in range(0, 103, 2)],
        )

    def open(self) -> None:
        if not libhackrf:
            raise BackendUnavailableError("libhackrf is not available.")

        dev_ptr = ctypes.c_void_p()
        if self._info.serial:
            res = libhackrf.hackrf_open_by_serial(
                self._info.serial.encode("utf-8"), ctypes.byref(dev_ptr)
            )
        else:
            res = libhackrf.hackrf_open(ctypes.byref(dev_ptr))

        if res != HACKRF_ERROR_OK:
            raise BackendError(f"Failed to open HackRF: {res}")

        self._dev = dev_ptr

        # Disable amp for safety
        libhackrf.hackrf_set_amp_enable(self._dev, 0)

    def close(self) -> None:
        assert libhackrf is not None
        if self._dev:
            libhackrf.hackrf_close(self._dev)
            self._dev = None

    def set_frequency(self, frequency: int) -> None:
        assert libhackrf is not None
        if not self._dev:
            raise BackendError("Device not open")
        if frequency < 1_000_000 or frequency > 6_000_000_000:
            raise ValueError(f"Frequency {frequency} out of HackRF range (1MHz-6GHz)")
        res = libhackrf.hackrf_set_freq(self._dev, int(frequency))
        if res != HACKRF_ERROR_OK:
            raise BackendError(f"Failed to set frequency: {res}")
        self._freq = frequency

    def get_frequency(self) -> int:
        return self._freq

    def set_sample_rate(self, sample_rate: int) -> None:
        assert libhackrf is not None
        if not self._dev:
            raise BackendError("Device not open")
        if sample_rate < 2_000_000 or sample_rate > 20_000_000:
            raise ValueError(f"Sample rate {sample_rate} out of HackRF range (2M-20M)")
        res = libhackrf.hackrf_set_sample_rate(self._dev, float(sample_rate))
        if res != HACKRF_ERROR_OK:
            raise BackendError(f"Failed to set sample rate: {res}")
        self._rate = sample_rate

        # Auto baseband filter: commonly set to ~75% of sample rate
        bw = int(sample_rate * 0.75)
        # HackRF sets BW in discrete steps. We let libhackrf choose the nearest.
        libhackrf.hackrf_set_baseband_filter_bandwidth(self._dev, bw)

    def get_sample_rate(self) -> int:
        return self._rate

    def set_gain(self, gain: float) -> None:
        assert libhackrf is not None
        if not self._dev:
            raise BackendError("Device not open")

        target = max(0, min(102, int(gain)))
        # Allocate up to 40 dB to LNA (in 8 dB steps) for better NF
        lna = min(40, (target // 8) * 8)
        # Allocate remainder to VGA (in 2 dB steps, up to 62 dB)
        vga = min(62, (target - lna) // 2 * 2)

        res = libhackrf.hackrf_set_lna_gain(self._dev, lna)
        if res != HACKRF_ERROR_OK:
            raise BackendError(f"Failed to set LNA gain: {res}")

        res = libhackrf.hackrf_set_vga_gain(self._dev, vga)
        if res != HACKRF_ERROR_OK:
            raise BackendError(f"Failed to set VGA gain: {res}")

        self._gain = float(lna + vga)

    def get_gain(self) -> float:
        return self._gain

    def stream(self, config: "StreamConfig | None" = None) -> IQStream:
        if config:
            self.set_frequency(config.frequency)
            self.set_sample_rate(config.sample_rate)
            if config.gain is not None:
                if isinstance(config.gain, str) and config.gain.lower() == "auto":
                    self.set_gain(40.0)  # Sensible default for auto
                else:
                    self.set_gain(float(config.gain))

        cfg = StreamConfig(
            frequency=self._freq,
            sample_rate=self._rate,
            gain=self._gain,
        )
        return HackRFStream(self, cfg)


class HackRFBackend(SDRBackend):
    def __init__(self):
        self._initialized = False

    @property
    def name(self) -> str:
        return "hackrf"

    def _init_lib(self) -> bool:
        if self._initialized:
            return True
        if not libhackrf:
            return False
        res = libhackrf.hackrf_init()
        if res != HACKRF_ERROR_OK:
            return False
        self._initialized = True
        return True

    def detect(self) -> List[DeviceInfo]:
        if not self._init_lib():
            return []

        assert libhackrf is not None
        devices = []
        device_list_ptr = libhackrf.hackrf_device_list()

        if not device_list_ptr:
            return []

        try:
            device_list = device_list_ptr.contents
            for i in range(device_list.devicecount):
                serial_ptr = device_list.serial_numbers[i]
                serial = ""
                if serial_ptr:
                    serial = ctypes.string_at(serial_ptr).decode("utf-8")

                info = DeviceInfo(
                    driver="hackrf",
                    product="HackRF One",
                    vendor="Great Scott Gadgets",
                    serial=serial if serial else str(i),
                    bus=None,
                    usb_vid=None,
                    usb_pid=None,
                )
                devices.append(info)
        finally:
            libhackrf.hackrf_device_list_free(device_list_ptr)

        return devices

    def open(self, device_info: DeviceInfo) -> SDRDevice:
        if not self._init_lib():
            raise BackendUnavailableError("libhackrf unavailable")

        dev = HackRFDevice(device_info)
        dev.open()
        return dev

    def __del__(self):
        if self._initialized and libhackrf:
            try:
                libhackrf.hackrf_exit()
            except Exception:
                pass
            self._initialized = False
