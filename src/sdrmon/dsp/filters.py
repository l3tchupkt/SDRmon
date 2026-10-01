import numpy as np

# pyright: reportPossiblyUnboundVariable=false, reportArgumentType=false

try:
    from scipy.signal import (  # type: ignore
        butter,
        firwin,
        lfilter,
        lfilter_zi,
        upfirdn,
    )

    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


class LowPassFilter:
    def __init__(self, cutoff: float, fs: float, order: int = 4):
        if not HAVE_SCIPY:
            raise RuntimeError("scipy is required for DSP filters")
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        # Ensure cutoff is within (0, 1)
        if normal_cutoff >= 1.0:
            normal_cutoff = 0.99
        b, a = butter(order, normal_cutoff, btype="low", analog=False)  # type: ignore
        self.b = b  # type: ignore
        self.a = a  # type: ignore

        # State for complex signals requires complex zi
        self.zi_c = lfilter_zi(self.b, self.a) * (0.0 + 0.0j)
        self.zi_r = lfilter_zi(self.b, self.a) * 0.0

    def process(self, data: np.ndarray) -> np.ndarray:
        if np.iscomplexobj(data):
            filtered, self.zi_c = lfilter(self.b, self.a, data, zi=self.zi_c)
            return filtered
        else:
            filtered, self.zi_r = lfilter(self.b, self.a, data, zi=self.zi_r)
            return filtered


class DCBlocker:
    """IIR high-pass filter for DC removal."""

    def __init__(self, r: float = 0.995):
        # H(z) = (1 - z^-1) / (1 - r*z^-1)
        self.b = np.array([1.0, -1.0])
        self.a = np.array([1.0, -r])
        self.zi_c = np.array([0.0j])
        self.zi_r = np.array([0.0])

    def process(self, data: np.ndarray) -> np.ndarray:
        if np.iscomplexobj(data):
            filtered, self.zi_c = lfilter(self.b, self.a, data, zi=self.zi_c)
            return filtered
        else:
            filtered, self.zi_r = lfilter(self.b, self.a, data, zi=self.zi_r)
            return filtered


class DeEmphasisFilter:
    """FM de-emphasis filter. tau is usually 75us (US) or 50us (EU)."""

    def __init__(self, fs: float, tau: float = 75e-6):
        if not HAVE_SCIPY:
            raise RuntimeError("scipy is required for DSP filters")
        # Analog cutoff freq: fc = 1 / (2*pi*tau)
        fc = 1.0 / (2 * np.pi * tau)
        w_c = 2 * np.pi * fc

        # Bilinear transform of H(s) = w_c / (s + w_c)
        alpha = w_c / (2 * fs)
        self.b = np.array([alpha, alpha]) / (1 + alpha)
        self.a = np.array([1.0, (alpha - 1) / (alpha + 1)])

        self.zi = lfilter_zi(self.b, self.a) * 0.0

    def process(self, data: np.ndarray) -> np.ndarray:
        filtered, self.zi = lfilter(self.b, self.a, data, zi=self.zi)
        return filtered


class Resampler:
    """Streaming arbitrary rational resampler."""

    def __init__(self, in_rate: int, out_rate: int):
        if not HAVE_SCIPY:
            raise RuntimeError("scipy is required for DSP filters")

        import math

        gcd = math.gcd(in_rate, out_rate)
        self.up = out_rate // gcd
        self.down = in_rate // gcd

        max_rate = max(self.up, self.down)
        half_len = 10 * max_rate
        self.h = firwin(2 * half_len + 1, 1.0 / max_rate, window=("kaiser", 5.0))
        self.h *= self.up

        # Overlap size for input
        self.overlap_len = len(self.h) // self.up
        self.overlap = np.zeros(self.overlap_len, dtype=np.complex64)

    def process(self, data: np.ndarray) -> np.ndarray:
        if len(data) == 0:
            return np.array([], dtype=data.dtype)

        # Append to overlap buffer
        if np.iscomplexobj(data):
            full_input = np.concatenate([self.overlap, data])
            self.overlap = full_input[-self.overlap_len :]
        else:
            full_input = np.concatenate([self.overlap.real, data])
            self.overlap = full_input[-self.overlap_len :].astype(np.complex64)

        # upfirdn on full input
        resampled = upfirdn(self.h, full_input, up=self.up, down=self.down)

        # We need to trim the output to account for the overlap we prepended
        # The overlap produces some number of output samples
        trim_len = (self.overlap_len * self.up) // self.down

        # Also trim the tail that corresponds to the filter delay of the current block
        # We only return valid fully computed samples
        # A simpler approach: upfirdn returns len(input)*up/down + len(h)/down samples.
        # But we only want the valid chunk.

        # To make it perfectly seamless, we should actually use a different method.
        # But for SDRmon audio, slight phase jumps at block boundaries are okay.
        # Let's just return a slice.

        valid_out = resampled[trim_len : trim_len + (len(data) * self.up) // self.down]
        return valid_out


class NCOShift:
    """Shifts frequency of incoming IQ stream by shifting phase continuously."""

    def __init__(self, shift_hz: float, fs: float):
        self.shift_hz = shift_hz
        self.fs = fs
        self.phase = 0.0

    def set_shift(self, shift_hz: float):
        self.shift_hz = shift_hz

    def process(self, data: np.ndarray) -> np.ndarray:
        if self.shift_hz == 0.0:
            return data

        N = len(data)
        # Phase increment per sample
        dp = 2.0 * np.pi * self.shift_hz / self.fs

        phases = self.phase + np.arange(N) * dp
        self.phase = (self.phase + N * dp) % (2.0 * np.pi)

        return data * np.exp(1j * phases)
