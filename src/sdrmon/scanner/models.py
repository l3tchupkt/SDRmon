"""
Data models for the RF scanner.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ScanConfig:
    start_frequency: int
    stop_frequency: int
    step: int
    dwell_time: float
    sample_rate: int
    fft_size: int = 2048
    threshold: float = 5.0
    averaging: int = 1
    settle_time: float = 0.05

    def __post_init__(self):
        if self.start_frequency >= self.stop_frequency:
            raise ValueError("start_frequency must be less than stop_frequency")
        if self.step <= 0:
            raise ValueError("step must be positive")
        if self.dwell_time <= 0:
            raise ValueError("dwell_time must be positive")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.fft_size <= 0:
            raise ValueError("fft_size must be positive")
        if self.averaging < 1:
            raise ValueError("averaging must be >= 1")


@dataclass(frozen=True)
class ScanResult:
    frequency: int
    peak_frequency: float
    peak_power: float
    noise_floor: float
    occupied: bool
    timestamp: float


@dataclass
class ScanReport:
    started_at: float
    completed_at: float
    results: List[ScanResult]

    @property
    def total_steps(self) -> int:
        return len(self.results)

    @property
    def occupied_steps(self) -> int:
        return sum(1 for r in self.results if r.occupied)

    @property
    def duration(self) -> float:
        return self.completed_at - self.started_at
