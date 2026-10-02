import time
from dataclasses import dataclass

import numpy as np


@dataclass
class SignalCandidate:
    frequency: float
    power: float
    bandwidth: float
    confidence: float
    timestamp: float


class SignalDetector:
    def __init__(
        self,
        sdr_rate: float,
        min_prominence_db: float = 5.0,
        min_bandwidth: float = 5000.0,
    ):
        self.sdr_rate = sdr_rate
        self.min_prominence_db = min_prominence_db
        self.min_bandwidth = min_bandwidth

        self.noise_floor_db = -100.0
        self.threshold_db = -90.0

    def detect(self, psd: np.ndarray, sdr_center: float) -> list[SignalCandidate]:
        if len(psd) == 0:
            return []

        # 1. Estimate noise floor using a percentile (e.g., 20th percentile)
        # This is more robust against many signals taking up bandwidth than mean/median
        self.noise_floor_db = float(np.percentile(psd, 20))
        self.threshold_db = self.noise_floor_db + self.min_prominence_db

        # 2. Find regions above threshold
        above_thresh = psd > self.threshold_db

        candidates = []
        in_signal = False
        start_idx = 0

        for i, is_above in enumerate(above_thresh):
            if is_above and not in_signal:
                in_signal = True
                start_idx = i
            elif not is_above and in_signal:
                in_signal = False
                end_idx = i

                # We have a candidate region
                region = psd[start_idx:end_idx]
                if len(region) == 0:
                    continue

                peak_idx = start_idx + np.argmax(region)
                peak_pwr = psd[peak_idx]

                # Calculate bandwidth based on bin count
                bin_hz = self.sdr_rate / len(psd)
                bw = (end_idx - start_idx) * bin_hz

                if bw >= self.min_bandwidth:
                    # Calculate actual frequency of peak
                    # psd is usually shifted such that center is at len(psd)//2
                    freq_offset = (peak_idx - len(psd) / 2.0) * bin_hz
                    freq = sdr_center + freq_offset

                    confidence = peak_pwr - self.noise_floor_db

                    candidates.append(
                        SignalCandidate(
                            frequency=float(freq),
                            power=float(peak_pwr),
                            bandwidth=float(bw),
                            confidence=float(confidence),
                            timestamp=time.time(),
                        )
                    )

        # If signal reaches the end of the PSD array
        if in_signal:
            end_idx = len(psd)
            region = psd[start_idx:end_idx]
            if len(region) > 0:
                peak_idx = start_idx + np.argmax(region)
                peak_pwr = psd[peak_idx]
                bin_hz = self.sdr_rate / len(psd)
                bw = (end_idx - start_idx) * bin_hz

                if bw >= self.min_bandwidth:
                    freq_offset = (peak_idx - len(psd) / 2.0) * bin_hz
                    freq = sdr_center + freq_offset
                    confidence = peak_pwr - self.noise_floor_db

                    candidates.append(
                        SignalCandidate(
                            frequency=float(freq),
                            power=float(peak_pwr),
                            bandwidth=float(bw),
                            confidence=float(confidence),
                            timestamp=time.time(),
                        )
                    )

        return candidates


def suggest_mode(bandwidth: float) -> str:
    """Provides a basic bandwidth-based suggestion."""
    if bandwidth < 15000:
        return "NFM"
    elif bandwidth > 100000:
        return "WFM"
    else:
        return "AM"
