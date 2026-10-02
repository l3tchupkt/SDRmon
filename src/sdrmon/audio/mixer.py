import numpy as np


class AudioMixer:
    """
    Mixes multiple audio streams into a single AudioOutput.
    Prevents clipping by normalizing/limiting the sum of all channels.
    The output property is callable so the owner can swap it at runtime.
    """

    def __init__(self, get_output):
        """get_output: a callable that returns the current AudioOutput."""
        self._get_output = get_output
        # Keep track of recent max amplitude for simple AGC/limiter
        self._peak_env = 0.0
        self._decay = 0.999

    def mix_and_write(self, channel_audio: list[np.ndarray]):
        """
        Mixes a list of audio arrays (one per channel) and writes to AudioOutput.
        Assumes all arrays are the same length.
        """
        if not channel_audio:
            return

        # Check if we actually have data
        length = len(channel_audio[0])
        if length == 0:
            return

        # Mix the arrays together
        mixed = np.zeros(length, dtype=np.float32)
        for audio in channel_audio:
            if len(audio) == length:
                mixed += audio

        # Simple fast-attack slow-decay limiter
        peak = np.max(np.abs(mixed))
        if peak > self._peak_env:
            self._peak_env = peak  # Fast attack
        else:
            self._peak_env = self._peak_env * self._decay + peak * (
                1.0 - self._decay
            )  # Slow decay

        if self._peak_env > 1.0:
            # Scale down to prevent clipping
            # Allow some headroom (0.95)
            mixed *= 0.95 / self._peak_env

        # Write to output
        self._get_output().write(mixed)
