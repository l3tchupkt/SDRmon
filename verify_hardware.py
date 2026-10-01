import time
from sdrmon.native.manager import NativeSDRManager
from sdrmon.core.settings import StreamConfig
from sdrmon.dsp.channel import ChannelManager, Channel
from sdrmon.audio.output import SoundDeviceAudioOutput

def main():
    print("Opening FakeSDR...")
    mgr = NativeSDRManager()
    dev = mgr.open("fake:0")
    
    config = StreamConfig(
        frequency=100_000_000,
        sample_rate=2_000_000,
        gain=0.0
    )
    dev.set_sample_rate(config.sample_rate)
    dev.set_frequency(config.frequency)
    
    print("Opening Audio Output...")
    audio = SoundDeviceAudioOutput()
    audio.open(None, 48000)
    audio.start()
    
    print("Setting up DSP...")
    cm = ChannelManager(config.sample_rate, 48000)
    
    # Add an FM channel at +500kHz offset
    ch = Channel(
        mode="wfm", 
        frequency=100_500_000, 
        sdr_rate=config.sample_rate, 
        audio_rate=48000
    )
    ch.squelch = -80
    ch.volume = 0.5
    cm.add_channel(ch)
    
    stream = dev.stream(config)
    stream.start()
    
    start_time = time.time()
    try:
        while time.time() - start_time < 5.0:
            block = stream.next_block()
            if block:
                audios = cm.process(block.samples)
                for aud in audios:
                    audio.write(aud)
    except KeyboardInterrupt:
        pass
    
    print("Stopping...")
    stream.stop()
    audio.stop()
    
    print("Stats:")
    print(f"Total IQ blocks read: Unknown (completed successfully)")
    print(f"Audio stats: {audio.get_stats()}")
    dev.close()
    
if __name__ == "__main__":
    main()
