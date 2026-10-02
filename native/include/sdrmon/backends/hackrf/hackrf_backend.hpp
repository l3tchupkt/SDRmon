#pragma once

#include "sdrmon/core/backend.hpp"
#include <memory>

namespace sdrmon {
namespace backends {

class HackRFBackend : public SDRBackend {
public:
    HackRFBackend();
    ~HackRFBackend() override;

    std::string name() const override;
    bool available() const override;
    
    std::vector<DeviceInfo> discover() override;
    std::shared_ptr<SDRDevice> open(const std::string& identifier) override;

private:
    bool initialized_ = false;
};

} // namespace backends
} // namespace sdrmon
