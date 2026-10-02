import numpy as np

from sdrmon.dsp.demod import create_demodulator
from sdrmon.dsp.filters import LowPassFilter, NCOShift


class Channel:
    def __init__(
        self,
        channel_id: int,
        mode: str,
        frequency: int,
        bandwidth: float,
        sdr_rate: int,
        audio_rate: int,
    ):
        self.channel_id = channel_id
        self.mode = mode.upper()
        self.frequency = frequency
        self.bandwidth = bandwidth
        self.sdr_rate = sdr_rate
        self.audio_rate = audio_rate
        self.muted = False
        self.enabled = True
        self.volume = 1.0
        self.squelch = -100.0  # dBFS

        self.nco = NCOShift(0.0, sdr_rate)
        self.channel_filter = LowPassFilter(self._get_bandwidth() / 2, sdr_rate)
        self.demod = create_demodulator(mode, sdr_rate, audio_rate)

    def _get_bandwidth(self) -> float:
        if self.bandwidth > 0:
            return self.bandwidth
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

        if pwr_db < self.squelch or self.muted or not self.enabled:
            return np.zeros(
                int(len(iq) * self.audio_rate / self.sdr_rate), dtype=np.float32
            )

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
        self.channels: dict[int, Channel] = {}
        self._next_id = 1

    def create_channel(
        self, frequency: int, mode: str, bandwidth: float = 0.0
    ) -> Channel:
        ch = Channel(
            self._next_id, mode, frequency, bandwidth, self.sdr_rate, self.audio_rate
        )
        self._next_id += 1
        ch.set_sdr_center(self.sdr_center)
        self.channels[ch.channel_id] = ch
        return ch

    def remove_channel(self, channel_id: int):
        if channel_id in self.channels:
            del self.channels[channel_id]

    def get_channel(self, channel_id: int) -> Channel | None:
        return self.channels.get(channel_id)

    def list_channels(self) -> list[Channel]:
        return list(self.channels.values())

    def enable_channel(self, channel_id: int):
        if ch := self.get_channel(channel_id):
            ch.enabled = True

    def disable_channel(self, channel_id: int):
        if ch := self.get_channel(channel_id):
            ch.enabled = False

    def clear(self):
        self.channels.clear()

    def set_sdr_center(self, center_hz: int):
        self.sdr_center = center_hz
        for ch in self.channels.values():
            ch.set_sdr_center(center_hz)

    def set_sdr_rate(self, sdr_rate: int):
        self.sdr_rate = sdr_rate
        # Recreate channels to update filters
        old_channels = list(self.channels.values())
        self.clear()
        for ch in old_channels:
            new_ch = self.create_channel(ch.frequency, ch.mode, ch.bandwidth)
            new_ch.muted = ch.muted
            new_ch.enabled = ch.enabled
            new_ch.volume = ch.volume
            new_ch.squelch = ch.squelch

    def process(self, iq: np.ndarray) -> list[np.ndarray]:
        return [ch.process(iq) for ch in self.channels.values()]
