#pragma once

#include <utility>
#include <vector>

namespace sdrmon {

struct Capabilities {
    bool has_rx{true};
    bool has_tx{false};
    
    std::vector<std::pair<double, double>> supported_sample_rates;
    std::vector<std::pair<double, double>> supported_frequencies;
    
    bool has_gain{true};
    std::vector<double> supported_gains;
    
    bool has_bandwidth{false};
    std::vector<std::pair<double, double>> supported_bandwidths;
    
    bool has_frequency_correction{false};
    bool has_hardware_agc{false};
    bool supports_streaming{true};
};

} // namespace sdrmon
