import pytest
import numpy as np

from sdrmon.backends.hackrf.backend import HackRFBackend

@pytest.mark.hardware
def test_hackrf_hardware_lifecycle():
    backend = HackRFBackend()
    
    # Discovery
    devices = backend.detect()
    if not devices:
        pytest.skip("Hardware test skipped: no HackRF detected.")
        
    info = devices[0]
    dev = backend.open(info)
    
    try:
        # Config
        dev.set_frequency(100_000_000)
        assert dev.get_frequency() == 100_000_000
        
        dev.set_sample_rate(2_000_000)
        assert dev.get_sample_rate() == 2_000_000
        
        dev.set_gain(20.0) # Should set LNA=16, VGA=4
        assert dev.get_gain() == 20.0
        
        # Streaming
        with dev.stream() as stream:
            # First block
            block = stream.read(timeout=2.0)
            
            assert isinstance(block.samples, np.ndarray)
            assert block.samples.dtype == np.complex64
            assert block.sample_rate == 2_000_000
            assert block.center_frequency == 100_000_000
            
            # Read a few more to verify sequence
            block2 = stream.read(timeout=2.0)
            assert block2.sequence_number > block.sequence_number
            
    finally:
        dev.close()
