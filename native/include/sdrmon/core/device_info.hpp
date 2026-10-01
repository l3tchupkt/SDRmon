#pragma once

#include <string>
#include "capabilities.hpp"

namespace sdrmon {

struct DeviceInfo {
    std::string backend_name;
    std::string identifier; // E.g., serial or path
    std::string serial;
    std::string display_name;
    std::string manufacturer;
    std::string product;
    Capabilities capabilities;
};

} // namespace sdrmon
