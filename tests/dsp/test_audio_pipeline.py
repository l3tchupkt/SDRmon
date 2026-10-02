import time

import pytest

from sdrmon.audio.output import NullAudioOutput
from sdrmon.core.settings import StreamConfig
from sdrmon.native.manager import NativeSDRManager
from sdrmon.ui.controller import UIController


class MockApp:
    def post_message(self, msg):
        pass


@pytest.mark.asyncio
async def test_fake_sdr_audio_pipeline():
    # 1. Fake SDR
    manager = NativeSDRManager()
    sdr = manager.open("fake:0")
    config = StreamConfig(frequency=100_000_000, sample_rate=1_000_000, gain=20.0)

    # 2. UIController
    app = MockApp()
    controller = UIController(sdr, app, config)
    controller.audio_out = NullAudioOutput()  # Mock audio

    # Add a channel (NFM at 100MHz)
    controller.channel_manager.create_channel(100_000_000, "NFM", 12500.0)
    # Disable squelch for test
    ch = list(controller.channel_manager.channels.values())[0]
    ch.squelch = -200.0

    # 3. Start pipeline
    controller.start()

    # Run for 0.5s to generate some audio
    time.sleep(0.5)

    # 4. Stop and verify
    controller.stop()

    stats = controller.audio_out.get_stats()
    total_samples = stats["total_samples"]

    # The SDR produces samples. With 1Msps, 0.5s is 500,000 IQ samples.
    # We decimate to 48000 Hz, so we expect around 24,000 audio samples.
    assert total_samples > 0
    assert total_samples > 10000, f"Expected many audio samples, got {total_samples}"
