import numpy as np

from sdrmon.ui.rendering import aggregate_spectrum, normalize_power


def test_aggregate_spectrum():
    power = np.array([-10.0, -20.0, -30.0, -5.0, -15.0, -25.0])

    # Same width
    res = aggregate_spectrum(power, display_width=6, min_power=-100.0)
    assert len(res) == 6
    np.testing.assert_allclose(res, power)

    # Smaller width
    res = aggregate_spectrum(power, display_width=3, min_power=-100.0)
    assert len(res) == 3
    # chunks: [-10, -20], [-30, -5], [-15, -25]
    # maxes: -10, -5, -15
    np.testing.assert_allclose(res, [-10.0, -5.0, -15.0])

    # Larger width
    res = aggregate_spectrum(power, display_width=10, min_power=-100.0)
    assert len(res) == 10
    np.testing.assert_allclose(res[:6], power)
    np.testing.assert_allclose(res[6:], -100.0)


def test_aggregate_spectrum_empty():
    res = aggregate_spectrum(np.array([]), display_width=5, min_power=-50.0)
    assert len(res) == 5
    np.testing.assert_allclose(res, -50.0)


def test_normalize_power():
    power = np.array([-100.0, -50.0, 0.0])
    res = normalize_power(power, -100.0, 0.0)

    assert res.dtype == np.uint8
    assert res[0] == 0
    assert res[1] == 127
    assert res[2] == 255

    # Out of bounds
    power_out = np.array([-120.0, 50.0])
    res_out = normalize_power(power_out, -100.0, 0.0)
    assert res_out[0] == 0
    assert res_out[1] == 255
