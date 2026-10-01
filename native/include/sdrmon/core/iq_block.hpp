#pragma once

#include <vector>
#include <complex>
#include <cstdint>

namespace sdrmon {

struct IQBlock {
    std::vector<std::complex<float>> data;
    uint64_t sequence_number{0};
    size_t sample_count{0};
    double sample_rate{0.0};
    double center_frequency{0.0};
    double timestamp{0.0};
};

} // namespace sdrmon
