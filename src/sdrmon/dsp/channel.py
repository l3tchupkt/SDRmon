import numpy as np

from sdrmon.dsp.demod import create_demodulator
from sdrmon.dsp.filters import LowPassFilter, NCOShift


class Channel:
    def __init__(self, mode: str, frequency: int, sdr_rate: int, audio_rate: int):
        self.mode = mode.upper()
        self.frequency = frequency
        self.sdr_rate = sdr_rate
        self.audio_rate = audio_rate
        self.muted = False
        self.volume = 1.0
        self.squelch = -100.0  # dBFS

        self.nco = NCOShift(0.0, sdr_rate)
        self.channel_filter = LowPassFilter(self._get_bandwidth() / 2, sdr_rate)
        self.demod = create_demodulator(mode, sdr_rate, audio_rate)

    def _get_bandwidth(self) -> float:
        if self.mode == "AM":
            return 10000.0
        elif self.mode == "NFM":
            return 12500.0
        else:  # FM, WFM
            return 200000.0

    def set_sdr_center(self, center_hz: int):
        # We need to shift the target frequency down to 0 Hz.
        # e.g., if SDR is 100M and channel is 101M, we need to shift by -1M.
        shift = self.frequency - center_hz
        self.nco.set_shift(-shift)

    def process(self, iq: np.ndarray) -> np.ndarray:
        if len(iq) == 0:
            return np.array([], dtype=np.float32)

        pwr = np.mean(np.abs(iq) ** 2)
        if pwr > 0:
            pwr_db = 10 * np.log10(pwr)
        else:
            pwr_db = -100.0

        # Shift to baseband
        shifted = self.nco.process(iq)
        # Filter channel
        filtered = self.channel_filter.process(shifted)
        # Demodulate & resample
        audio = self.demod.process(filtered)

        if pwr_db < self.squelch or self.muted:
            return np.zeros_like(audio)

        return audio * self.volume


class ChannelManager:
    def __init__(self, sdr_rate: int, audio_rate: int):
        self.sdr_rate = sdr_rate
        self.audio_rate = audio_rate
        self.sdr_center = 100_000_000
        self.channels: list[Channel] = []

    def add_channel(self, channel: Channel):
        channel.set_sdr_center(self.sdr_center)
        self.channels.append(channel)

    def clear(self):
        self.channels.clear()

    def set_sdr_center(self, center_hz: int):
        self.sdr_center = center_hz
        for ch in self.channels:
            ch.set_sdr_center(center_hz)

    def set_sdr_rate(self, sdr_rate: int):
        self.sdr_rate = sdr_rate
        # Recreate channels to update filters
        old_channels = self.channels
        self.clear()
        for ch in old_channels:
            new_ch = Channel(ch.mode, ch.frequency, self.sdr_rate, self.audio_rate)
            new_ch.muted = ch.muted
            new_ch.volume = ch.volume
            new_ch.squelch = ch.squelch
            self.add_channel(new_ch)

    def process(self, iq: np.ndarray) -> list[np.ndarray]:
        return [ch.process(iq) for ch in self.channels]
