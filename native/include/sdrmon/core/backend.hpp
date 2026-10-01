#pragma once

#include <vector>
#include <string>
#include <memory>
#include "device.hpp"

namespace sdrmon {

class SDRBackend {
public:
    virtual ~SDRBackend() = default;

    virtual std::string name() const = 0;
    virtual bool available() const = 0;
    
    virtual std::vector<DeviceInfo> discover() = 0;
    virtual std::shared_ptr<SDRDevice> open(const std::string& identifier) = 0;
};

} // namespace sdrmon
