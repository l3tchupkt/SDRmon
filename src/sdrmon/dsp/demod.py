import numpy as np

from sdrmon.dsp.filters import DCBlocker, DeEmphasisFilter, LowPassFilter, Resampler


class AMDemodulator:
    def __init__(self, in_rate: int, out_rate: int, bandwidth: float = 10000.0):
        self.in_rate = in_rate
        self.out_rate = out_rate
        self.dc_blocker = DCBlocker()
        self.lowpass = LowPassFilter(bandwidth / 2, in_rate)
        self.resampler = Resampler(in_rate, out_rate)

    def process(self, iq: np.ndarray) -> np.ndarray:
        if len(iq) == 0:
            return np.array([], dtype=np.float32)
        # Envelope detection
        mag = np.abs(iq)
        # Remove DC carrier
        audio = self.dc_blocker.process(mag)
        # Lowpass filter
        audio = self.lowpass.process(audio)
        # Resample to audio rate
        return self.resampler.process(audio)


class FMDemodulator:
    def __init__(
        self,
        in_rate: int,
        out_rate: int,
        bandwidth: float,
        deviation: float,
        tau: float = 0.0,
    ):
        self.in_rate = in_rate
        self.out_rate = out_rate
        self.last_sample = 0.0j

        self.gain = in_rate / (2.0 * np.pi * deviation) if deviation > 0 else 1.0
        self.deemph = DeEmphasisFilter(in_rate, tau) if tau > 0 else None
        self.lowpass = LowPassFilter(bandwidth / 2, in_rate)
        self.resampler = Resampler(in_rate, out_rate)

    def process(self, iq: np.ndarray) -> np.ndarray:
        if len(iq) == 0:
            return np.array([], dtype=np.float32)

        # Differentiate phase (discriminator)
        delayed = np.empty_like(iq)
        delayed[0] = self.last_sample
        delayed[1:] = iq[:-1]
        self.last_sample = iq[-1]

        # Phase difference
        phase_diff = np.angle(iq * np.conjugate(delayed))
        audio = phase_diff * self.gain

        # De-emphasis
        if self.deemph:
            audio = self.deemph.process(audio)

        # Lowpass
        audio = self.lowpass.process(audio)

        # Resample
        return self.resampler.process(audio)


def create_demodulator(
    mode: str, in_rate: int, out_rate: int
) -> AMDemodulator | FMDemodulator:
    mode = mode.upper()
    if mode == "AM":
        return AMDemodulator(in_rate, out_rate, bandwidth=10000.0)
    elif mode == "NFM":
        # NFM: ~12.5kHz bandwidth, 2.5kHz deviation, no de-emphasis typically
        return FMDemodulator(
            in_rate, out_rate, bandwidth=12500.0, deviation=2500.0, tau=0.0
        )
    elif mode == "FM":
        # FM (broadcast): ~200kHz bandwidth, 75kHz deviation, 75us de-emphasis
        return FMDemodulator(
            in_rate, out_rate, bandwidth=200000.0, deviation=75000.0, tau=75e-6
        )
    elif mode == "WFM":
        # WFM: same as broadcast FM
        return FMDemodulator(
            in_rate, out_rate, bandwidth=200000.0, deviation=75000.0, tau=75e-6
        )
    else:
        raise ValueError(f"Unsupported mode: {mode}")
