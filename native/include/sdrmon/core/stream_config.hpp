#pragma once

#include <optional>

namespace sdrmon {

struct StreamConfig {
    double center_frequency{100e6};
    double sample_rate{2.048e6};
    std::optional<double> bandwidth;
    
    enum class GainMode {
        Automatic,
        Manual
    };
    
    GainMode gain_mode{GainMode::Automatic};
    std::optional<double> gain_value;
    
    size_t block_size{16384};
    std::optional<int> frequency_correction_ppm;
};

} // namespace sdrmon
