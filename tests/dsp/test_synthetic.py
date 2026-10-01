import numpy as np
import pytest

from sdrmon.dsp.channel import Channel, ChannelManager


def generate_carrier(rate, freq, duration=0.1):
    t = np.arange(int(rate * duration)) / rate
    return np.exp(1j * 2 * np.pi * freq * t).astype(np.complex64)


def generate_am(rate, carrier_freq, mod_freq, duration=0.1):
    t = np.arange(int(rate * duration)) / rate
    # carrier * (1 + 0.5 * sin(2*pi*mod_freq*t))
    mod = 1.0 + 0.5 * np.sin(2 * np.pi * mod_freq * t)
    carrier = np.exp(1j * 2 * np.pi * carrier_freq * t)
    return (carrier * mod).astype(np.complex64)


def generate_fm(rate, carrier_freq, mod_freq, deviation, duration=0.1):
    t = np.arange(int(rate * duration)) / rate
    # phase integral of modulation
    # modulating signal = sin(2*pi*mod_freq*t)
    # phase = (deviation / mod_freq) * -cos(2*pi*mod_freq*t)
    phase = (deviation / mod_freq) * -np.cos(2 * np.pi * mod_freq * t)
    carrier_phase = 2 * np.pi * carrier_freq * t
    return np.exp(1j * (carrier_phase + phase)).astype(np.complex64)


def check_1khz_tone(audio, rate):
    if len(audio) < rate * 0.05:
        return False
    # FFT to find peak frequency
    f = np.fft.rfftfreq(len(audio), 1 / rate)
    Y = np.abs(np.fft.rfft(audio))
    peak_idx = np.argmax(Y)
    peak_f = f[peak_idx]
    # Check if peak is near 1000 Hz (allow some tolerance)
    return 950 <= peak_f <= 1050


@pytest.mark.parametrize("mode", ["AM", "NFM", "FM", "WFM"])
def test_demod_1khz(mode):
    sdr_rate = 1_000_000
    audio_rate = 48000

    mgr = ChannelManager(sdr_rate, audio_rate)
    mgr.set_sdr_center(100_000_000)

    ch = Channel(mode, 100_000_000, sdr_rate, audio_rate)
    # Turn off squelch for testing
    ch.squelch = -200.0
    mgr.add_channel(ch)

    if mode == "AM":
        iq = generate_am(sdr_rate, 0, 1000, duration=0.2)
    elif mode == "NFM":
        iq = generate_fm(sdr_rate, 0, 1000, 2500, duration=0.2)
    else:
        iq = generate_fm(sdr_rate, 0, 1000, 75000, duration=0.2)

    audio = mgr.process(iq)[0]

    # We should have generated some audio samples
    assert len(audio) > 0
    # Resampler delay might cause some initial silence/transients
    # Skip first 1000 samples
    audio_valid = audio[1000:]

    assert check_1khz_tone(audio_valid, audio_rate), (
        f"{mode} failed to decode 1kHz tone"
    )


def test_nco_offset():
    sdr_rate = 1_000_000
    audio_rate = 48000

    mgr = ChannelManager(sdr_rate, audio_rate)
    mgr.set_sdr_center(100_000_000)

    # Channel is at 100.1 MHz, which is a +100kHz offset
    ch = Channel("NFM", 100_100_000, sdr_rate, audio_rate)
    ch.squelch = -200.0
    mgr.add_channel(ch)

    # Generate FM at +100kHz
    iq = generate_fm(sdr_rate, 100_000, 1000, 2500, duration=0.2)
    audio = mgr.process(iq)[0]

    assert len(audio) > 0
    audio_valid = audio[1000:]
    assert check_1khz_tone(audio_valid, audio_rate), (
        "NCO offset failed to decode 1kHz tone"
    )
