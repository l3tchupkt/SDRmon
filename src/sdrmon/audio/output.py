# pyright: reportOptionalMemberAccess=false, reportPossiblyUnboundVariable=false
import abc
import queue
import threading

import numpy as np


class AudioOutput(abc.ABC):
    @abc.abstractmethod
    def discover(self) -> list[str]:
        pass

    @abc.abstractmethod
    def open(self, device_name: str | None, sample_rate: int):
        pass

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def write(self, samples: np.ndarray):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def get_stats(self) -> dict[str, float]:
        pass


class NullAudioOutput(AudioOutput):
    def __init__(self):
        self.sample_rate = 48000
        self.total_samples = 0
        self.underruns = 0

    def discover(self) -> list[str]:
        return ["Null Device"]

    def open(self, device_name: str | None, sample_rate: int):
        self.sample_rate = sample_rate
        self.total_samples = 0
        self.underruns = 0

    def start(self):
        pass

    def write(self, samples: np.ndarray):
        self.total_samples += len(samples)

    def stop(self):
        pass

    def close(self):
        pass

    def get_stats(self) -> dict[str, float]:
        return {
            "underruns": self.underruns,
            "total_samples": self.total_samples,
            "sample_rate": self.sample_rate,
        }


try:
    import sounddevice as sd

    HAVE_SOUNDDEVICE = True
except ImportError:
    sd = None  # type: ignore
    HAVE_SOUNDDEVICE = False


class SoundDeviceAudioOutput(AudioOutput):
    def __init__(self):
        if not HAVE_SOUNDDEVICE:
            raise RuntimeError("sounddevice is required for SoundDeviceAudioOutput")
        self.stream = None
        self.sample_rate = 48000
        
        self.underruns = 0
        self.overruns = 0
        self.generated_samples = 0
        self.played_samples = 0
        self.dropped_samples = 0
        
        self.q = queue.Queue(maxsize=100)  # Buffer of audio chunks
        self.thread = None
        self._running = False

    def discover(self) -> list[str]:
        devices = sd.query_devices()
        return [d["name"] for d in devices if d["max_output_channels"] > 0]

    def open(self, device_name: str | None, sample_rate: int):
        self.sample_rate = sample_rate
        self.device_name = device_name
        self.stream = sd.OutputStream(
            samplerate=sample_rate, channels=1, device=device_name
        )

    def _worker(self):
        while self._running:
            try:
                # Wait for data
                samples = self.q.get(timeout=0.1)
                if len(samples) > 0 and self.stream:
                    # Write blocks until device has consumed it
                    # This naturally keeps the queue bounded and pushes back
                    try:
                        self.stream.write(samples)
                        self.played_samples += len(samples)
                    except sd.PortAudioError as e:
                        if "underflow" in str(e).lower():
                            self.underruns += 1
                        self.played_samples += len(samples) # Still advance
            except queue.Empty:
                pass
            except Exception:
                pass

    def start(self):
        self._running = True
        self.underruns = 0
        self.overruns = 0
        self.generated_samples = 0
        self.played_samples = 0
        self.dropped_samples = 0
        
        if self.stream:
            self.stream.start()

        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def write(self, samples: np.ndarray):
        if not self._running:
            return

        self.generated_samples += len(samples)
        try:
            # If queue is full, we drop the oldest to avoid blocking DSP (and by extension IQ stream)
            if self.q.full():
                try:
                    dropped = self.q.get_nowait()
                    self.dropped_samples += len(dropped)
                    self.overruns += 1
                except queue.Empty:
                    pass
            self.q.put_nowait(samples)
        except queue.Full:
            self.dropped_samples += len(samples)
            self.overruns += 1

    def stop(self):
        self._running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.stream:
            self.stream.stop()

    def close(self):
        self.stop()
        if self.stream:
            self.stream.close()
            self.stream = None

    def get_stats(self) -> dict[str, float]:
        return {
            "underruns": self.underruns, 
            "overruns": self.overruns,
            "generated": self.generated_samples,
            "played": self.played_samples,
            "dropped": self.dropped_samples,
            "queue_depth": self.q.qsize()
        }
