"""
Example: Channel tuning and Demodulation using ChannelManager
"""
import numpy as np
from sdrmon.dsp.channel import ChannelManager
from sdrmon.core.samples import IQBlock

def main():
    # Input SDR sample rate
    input_rate = 2_000_000
    
    # Target audio output sample rate
    audio_rate = 48_000
    
    # Initialize the DSP manager
    manager = ChannelManager(input_rate, audio_rate)
    
    # We are tuned to 100 MHz, we want to demodulate WFM at 100.5 MHz
    center_freq = 100_000_000
    tuned_freq = 100_500_000
    
    # Set the channel configuration
    manager.set_tuning(tuned_freq, center_freq)
    manager.set_mode("wfm")
    manager.set_squelch(-60.0)
    
    # Generate some synthetic FM-modulated IQ data
    print("Generating synthetic FM signal at +500 kHz...")
    num_samples = 32768
    t = np.arange(num_samples) / input_rate
    
    # Carrier offset
    offset = tuned_freq - center_freq
    carrier = np.exp(1j * 2 * np.pi * offset * t)
    
    # Modulation (440 Hz tone)
    mod_index = 75000.0 / 440.0
    audio_phase = mod_index * np.sin(2 * np.pi * 440 * t)
    
    samples = carrier * np.exp(1j * audio_phase)
    samples = samples.astype(np.complex64)
    
    block = IQBlock(
        samples=samples,
        sample_rate=input_rate,
        center_frequency=center_freq,
        gain=0.0,
        timestamp=0.0,
        sequence_number=0
    )
    
    # Process the block
    print("Demodulating...")
    audio_data = manager.process(block)
    
    if audio_data is not None and len(audio_data) > 0:
        print(f"Successfully generated {len(audio_data)} audio samples.")
        print(f"Max audio amplitude: {np.max(np.abs(audio_data)):.3f}")
    else:
        print("No audio data produced (possibly squelched).")

if __name__ == "__main__":
    main()
